"""OpenTimestamps anchoring of ledger checkpoints.

What is stamped: sha256(merkle_root_hex) of the newest un-anchored checkpoint.
Because every raw_records entry hash chains all earlier entries, anchoring the
newest checkpoint transitively timestamps the whole ledger up to its last_seq,
so one stamp per anchoring run is enough.

Lifecycle (ledger_checkpoints.ots_status):
  pending   - submitted to public calendars; proof holds PendingAttestations
  confirmed - upgrade() found a Bitcoin block-header attestation
  verified  - verify() matched the attested merkle root against the block
              header fetched from a public block explorer (no local node)
Stamping needs network access and ENABLE_OTS=true; otherwise nothing is
stamped and the reason is reported (never a fake proof).
"""
from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import urllib.request
from typing import Any

from app.config import settings

BLOCK_EXPLORER = "https://blockstream.info/api"


def _calendars() -> list[str]:
    return [c.strip() for c in settings.ots_calendars.split(",") if c.strip()]


def checkpoint_digest(merkle_root: str) -> bytes:
    return hashlib.sha256(merkle_root.encode()).digest()


def _serialize(dtf: Any) -> bytes:
    from opentimestamps.core.serialize import StreamSerializationContext

    buf = io.BytesIO()
    dtf.serialize(StreamSerializationContext(buf))
    return buf.getvalue()


def _deserialize(proof: bytes) -> Any:
    from opentimestamps.core.serialize import StreamDeserializationContext
    from opentimestamps.core.timestamp import DetachedTimestampFile

    return DetachedTimestampFile.deserialize(StreamDeserializationContext(io.BytesIO(proof)))


def stamp(merkle_root: str, calendars: list[str] | None = None, timeout: int = 10) -> bytes:
    """Submit to calendars; returns a serialized .ots proof (pending)."""
    from opentimestamps.calendar import RemoteCalendar
    from opentimestamps.core.op import OpSHA256
    from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

    digest = checkpoint_digest(merkle_root)
    dtf = DetachedTimestampFile(OpSHA256(), Timestamp(digest))
    ok = 0
    errors = []
    for url in calendars or _calendars():
        try:
            dtf.timestamp.merge(RemoteCalendar(url).submit(digest, timeout=timeout))
            ok += 1
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    if not ok:
        raise RuntimeError("no calendar accepted the digest: " + "; ".join(errors))
    return _serialize(dtf)


def attestations(proof: bytes) -> list[dict]:
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation, PendingAttestation

    dtf = _deserialize(proof)
    out = []
    for msg, att in dtf.timestamp.all_attestations():
        if isinstance(att, BitcoinBlockHeaderAttestation):
            out.append({"type": "bitcoin", "height": att.height, "msg": msg.hex()})
        elif isinstance(att, PendingAttestation):
            out.append({"type": "pending", "calendar": att.uri})
    return out


def upgrade(proof: bytes, timeout: int = 10) -> tuple[bytes, bool]:
    """Ask calendars for completed attestations. Returns (proof, changed)."""
    from opentimestamps.calendar import RemoteCalendar
    from opentimestamps.core.notary import PendingAttestation

    dtf = _deserialize(proof)
    changed = False
    for sub in list(_walk(dtf.timestamp)):
        for att in list(sub.attestations):
            if isinstance(att, PendingAttestation):
                try:
                    upgraded = RemoteCalendar(att.uri).get_timestamp(sub.msg, timeout=timeout)
                except Exception:
                    continue
                sub.merge(upgraded)
                changed = True
    return _serialize(dtf), changed


def _walk(ts: Any):
    yield ts
    for child in ts.ops.values():
        yield from _walk(child)


def _fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as r:  # noqa: S310 - fixed https host
        return r.read().decode()


def verify_bitcoin(proof: bytes, merkle_root: str, fetch=_fetch) -> dict:
    """Check the proof commits to this checkpoint and its Bitcoin attestation
    matches the block header merkle root reported by a block explorer."""
    dtf = _deserialize(proof)
    if dtf.file_digest != checkpoint_digest(merkle_root):
        return {"status": "FAIL", "reason": "proof is for a different merkle root"}
    btc = [a for a in attestations(proof) if a["type"] == "bitcoin"]
    if not btc:
        return {"status": "PENDING", "reason": "no Bitcoin attestation yet; run upgrade later"}
    for a in btc:
        block_hash = fetch(f"{BLOCK_EXPLORER}/block-height/{a['height']}").strip()
        header = json.loads(fetch(f"{BLOCK_EXPLORER}/block/{block_hash}"))
        # OTS messages are in internal byte order; explorers display reversed.
        if bytes.fromhex(a["msg"])[::-1].hex() == header["merkle_root"]:
            return {"status": "VERIFIED", "height": a["height"], "block_hash": block_hash,
                    "block_time": header.get("timestamp")}
    return {"status": "FAIL", "reason": "attested merkle root does not match block header"}


# -- DB integration ------------------------------------------------------------------
def anchor_pending_checkpoints(db_path: str) -> dict:
    if not settings.enable_ots:
        return {"skipped": "ENABLE_OTS=false"}
    with sqlite3.connect(db_path) as conn:
        # only the newest seal: through the chain it covers every earlier record, so older
        # unstamped seals never need their own anchor
        row = conn.execute(
            "SELECT id, merkle_root, ots_proof FROM ledger_checkpoints ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row or row[2] is not None:
            return {"stamped": 0}
        try:
            proof = stamp(row[1])
        except Exception as exc:
            return {"stamped": 0, "error": str(exc)}
        conn.execute(
            "UPDATE ledger_checkpoints SET ots_proof=?, ots_status='pending' WHERE id=?", (proof, row[0])
        )
        conn.commit()
    return {"stamped": 1, "checkpoint_id": row[0]}


def upgrade_all(db_path: str) -> dict:
    results = []
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, merkle_root, ots_proof FROM ledger_checkpoints "
            "WHERE ots_proof IS NOT NULL AND COALESCE(ots_status,'pending') != 'verified'"
        ).fetchall()
        for cid, root, proof in rows:
            proof, _ = upgrade(proof)
            v = verify_bitcoin(proof, root)
            status = {"VERIFIED": "verified", "PENDING": "pending"}.get(v["status"], "failed")
            conn.execute(
                "UPDATE ledger_checkpoints SET ots_proof=?, ots_status=?, ots_block=? WHERE id=?",
                (proof, status, v.get("height"), cid),
            )
            results.append({"checkpoint_id": cid, **v})
        conn.commit()
    return {"checked": len(results), "results": results}


def anchor_checkpoint(merkle_root: str) -> bytes | None:
    """Back-compat helper: stamp one root, None when disabled or offline."""
    if not settings.enable_ots:
        return None
    try:
        return stamp(merkle_root)
    except Exception:
        return None
