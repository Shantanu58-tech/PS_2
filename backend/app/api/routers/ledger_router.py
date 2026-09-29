from fastapi import APIRouter
import aiosqlite
from app.config import settings
from app.ledger.verify import verify_chain
import shutil, os

router = APIRouter()


@router.get("/ledger/status")
async def ledger_status():
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        count_row = await db.execute_fetchall("SELECT COUNT(*) as n FROM raw_records")
        cp_row = await db.execute_fetchall(
            "SELECT * FROM ledger_checkpoints ORDER BY id DESC LIMIT 1"
        )
    return {
        "record_count": count_row[0]["n"] if count_row else 0,
        "last_checkpoint": dict(cp_row[0]) if cp_row else None,
    }


@router.post("/ledger/verify")
async def ledger_verify():
    result = verify_chain(settings.db_path)
    return result


@router.post("/ledger/tamper-sim")
async def tamper_sim():
    scratch = settings.db_path.replace(".db", "_scratch.db")
    shutil.copy2(settings.db_path, scratch)
    import sqlite3
    with sqlite3.connect(scratch) as conn:
        row = conn.execute("SELECT seq, payload_canonical FROM raw_records ORDER BY RANDOM() LIMIT 1").fetchone()
        if not row:
            return {"error": "no records"}
        seq, payload = row
        tampered = payload[:-1] + ("X" if payload[-1] != "X" else "Y")
        conn.execute("UPDATE raw_records SET payload_canonical=? WHERE seq=?", (tampered, seq))
        conn.commit()
    result = verify_chain(scratch)
    os.remove(scratch)
    return {"tampered_seq": seq, "verify_result": result}
