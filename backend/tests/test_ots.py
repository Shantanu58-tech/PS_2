"""OpenTimestamps: stamping against a mocked calendar, attestation parsing,
Bitcoin verification against a mocked block explorer."""
import json

import pytest

from app.ledger import ots

ROOT_HEX = "ab" * 32


class FakeCalendar:
    """Returns a timestamp whose commitment is attested in a known Bitcoin block."""

    def __init__(self, url):
        self.url = url

    def submit(self, digest, timeout=None):
        from opentimestamps.core.notary import PendingAttestation
        from opentimestamps.core.timestamp import Timestamp

        ts = Timestamp(digest)
        ts.attestations.add(PendingAttestation(self.url))
        return ts


def test_disabled_by_default(db_path):
    assert ots.anchor_pending_checkpoints(db_path) == {"skipped": "ENABLE_OTS=false"}


def test_stamp_produces_pending_proof(monkeypatch):
    monkeypatch.setattr("opentimestamps.calendar.RemoteCalendar", FakeCalendar)
    proof = ots.stamp(ROOT_HEX, calendars=["https://cal.example"])
    atts = ots.attestations(proof)
    assert atts == [{"type": "pending", "calendar": "https://cal.example"}]


def test_stamp_fails_loudly_when_no_calendar(monkeypatch):
    class Down(FakeCalendar):
        def submit(self, digest, timeout=None):
            raise ConnectionError("offline")

    monkeypatch.setattr("opentimestamps.calendar.RemoteCalendar", Down)
    with pytest.raises(RuntimeError):
        ots.stamp(ROOT_HEX, calendars=["https://cal.example"])


def _bitcoin_proof(msg: bytes, height: int) -> bytes:
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
    from opentimestamps.core.op import OpAppend, OpSHA256
    from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

    digest = ots.checkpoint_digest(ROOT_HEX)
    root = Timestamp(digest)
    leaf = root.ops.add(OpAppend(b"\x01")).ops.add(OpSHA256())
    leaf.attestations.add(BitcoinBlockHeaderAttestation(height))
    return ots._serialize(DetachedTimestampFile(OpSHA256(), root)), leaf.msg


def test_verify_bitcoin_against_block_explorer():
    proof, msg = _bitcoin_proof(b"", 800000)
    header_root = msg[::-1].hex()

    def fetch(url):
        return "0000blockhash" if "block-height" in url else json.dumps({"merkle_root": header_root, "timestamp": 1})

    res = ots.verify_bitcoin(proof, ROOT_HEX, fetch=fetch)
    assert res["status"] == "VERIFIED" and res["height"] == 800000

    bad = ots.verify_bitcoin(proof, ROOT_HEX, fetch=lambda u: "h" if "height" in u else json.dumps({"merkle_root": "00" * 32}))
    assert bad["status"] == "FAIL"
    assert ots.verify_bitcoin(proof, "cd" * 32, fetch=fetch)["status"] == "FAIL"  # other root


def test_only_the_newest_checkpoint_is_stamped(db_path, monkeypatch):
    import sqlite3

    monkeypatch.setattr(ots.settings, "enable_ots", True)
    monkeypatch.setattr("opentimestamps.calendar.RemoteCalendar", FakeCalendar)
    monkeypatch.setattr(ots.settings, "ots_calendars", "https://cal.example")
    with sqlite3.connect(db_path) as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(ledger_checkpoints)")}
        base = {"first_seq": 1, "last_seq": 100, "signature": "s", "pubkey_id": "k", "created_at": "2026-01-01"}
        for i, root in ((1, "aa" * 32), (2, "bb" * 32)):
            row = {k: v for k, v in {**base, "id": i, "merkle_root": root}.items() if k in cols}
            c.execute(f"INSERT INTO ledger_checkpoints ({','.join(row)}) VALUES ({','.join('?' * len(row))})", list(row.values()))
    assert ots.anchor_pending_checkpoints(db_path) == {"stamped": 1, "checkpoint_id": 2}
    # newest already stamped: the older seal is covered through the chain and is left alone
    assert ots.anchor_pending_checkpoints(db_path) == {"stamped": 0}
    with sqlite3.connect(db_path) as c:
        assert c.execute("SELECT id FROM ledger_checkpoints WHERE ots_proof IS NOT NULL").fetchall() == [(2,)]
