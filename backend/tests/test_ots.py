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
