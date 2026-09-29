import asyncio
import os
import shutil
import sqlite3
import tempfile
import time

from fastapi import APIRouter, HTTPException

from app.api.deps import fetch_all, fetch_one
from app.config import settings
from app.ledger.audit import log_action
from app.ledger.verify import verify_chain

router = APIRouter()


@router.get("/ledger/status")
async def ledger_status():
    from app.ledger.sign import Signer

    count = await fetch_one("SELECT COUNT(*) AS n, MAX(seq) AS last_seq FROM raw_records")
    cp = await fetch_one(
        "SELECT id, first_seq, last_seq, merkle_root, signature, pubkey_id, created_at, ots_status, ots_block "
        "FROM ledger_checkpoints ORDER BY id DESC LIMIT 1")
    n_cp = await fetch_one("SELECT COUNT(*) AS n FROM ledger_checkpoints")
    return {
        "record_count": count["n"] if count else 0,
        "last_seq": count["last_seq"] if count else None,
        "checkpoint_count": n_cp["n"] if n_cp else 0,
        "last_checkpoint": cp,
        "pubkey_id": Signer().pubkey_id,
        "ots_enabled": settings.enable_ots,
    }


@router.get("/ledger/checkpoints")
async def checkpoints(limit: int = 50):
    rows = await fetch_all(
        "SELECT id, first_seq, last_seq, merkle_root, pubkey_id, created_at, ots_status, ots_block "
        "FROM ledger_checkpoints ORDER BY id DESC LIMIT ?", (limit,))
    return {"checkpoints": rows}


@router.post("/ledger/verify")
async def ledger_verify():
    t0 = time.perf_counter()
    result = await asyncio.to_thread(verify_chain, settings.db_path)
    result["seconds"] = round(time.perf_counter() - t0, 3)
    await asyncio.to_thread(log_action, settings.db_path, "analyst", "ledger_verify", {"status": result["status"]})
    return result


def tamper_scratch_copy(db_path: str, seq: int | None = None) -> dict:
    """Copy the DB, mutate one stored payload byte in the COPY, verify the copy.

    The copy lives in a temp dir and is deleted afterwards; the real ledger is
    never written (append-only triggers are only dropped on the copy)."""
    tmpdir = tempfile.mkdtemp(prefix="satya_tamper_")
    scratch = os.path.join(tmpdir, "scratch.db")
    try:
        with sqlite3.connect(db_path) as src, sqlite3.connect(scratch) as dst:
            src.backup(dst)
        with sqlite3.connect(scratch) as conn:
            conn.execute("DROP TRIGGER IF EXISTS raw_no_update")
            if seq is None:
                row = conn.execute(
                    "SELECT seq, payload_canonical FROM raw_records ORDER BY RANDOM() LIMIT 1").fetchone()
            else:
                row = conn.execute(
                    "SELECT seq, payload_canonical FROM raw_records WHERE seq=?", (seq,)).fetchone()
            if not row:
                return {"error": "no records"}
            seq, payload = row
            pos = len(payload) // 2
            tampered = payload[:pos] + ("X" if payload[pos] != "X" else "Y") + payload[pos + 1:]
            conn.execute("UPDATE raw_records SET payload_canonical=? WHERE seq=?", (tampered, seq))
            conn.commit()
        result = verify_chain(scratch)
        return {"tampered_seq": seq, "byte_offset": pos, "verify_result": result,
                "detected_at_expected_seq": result.get("seq") == seq, "scratch_copy": True}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@router.post("/ledger/tamper-sim")
async def tamper_sim(seq: int | None = None):
    result = await asyncio.to_thread(tamper_scratch_copy, settings.db_path, seq)
    if "error" in result:
        raise HTTPException(409, result["error"])
    await asyncio.to_thread(log_action, settings.db_path, "analyst", "tamper_simulation",
                            {"seq": result["tampered_seq"], "detected": result["verify_result"]["status"] == "FAIL"})
    return result


@router.get("/ledger/proof/{seq}")
async def inclusion_proof(seq: int):
    from app.ledger.proof import inclusion_proof as build

    proof = await asyncio.to_thread(build, settings.db_path, seq)
    if proof is None:
        raise HTTPException(404, "record not covered by a checkpoint yet")
    return proof


@router.post("/ledger/ots/upgrade")
async def ots_upgrade():
    from app.ledger.ots import upgrade_all

    return await asyncio.to_thread(upgrade_all, settings.db_path)


@router.post("/ledger/ots/anchor")
async def ots_anchor():
    from app.ledger.ots import anchor_pending_checkpoints

    return await asyncio.to_thread(anchor_pending_checkpoints, settings.db_path)


@router.get("/audit")
async def audit_log(limit: int = 100):
    return {"entries": await fetch_all("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))}
