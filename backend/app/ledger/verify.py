from __future__ import annotations
import hashlib
import sqlite3
import base64
from pathlib import Path
from app.ledger.canonical import canonical_json
from app.ledger.merkle import build_merkle_root
from app.ledger.sign import PUBLIC_KEY_PATH
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_public_key() -> Ed25519PublicKey:
    raw = PUBLIC_KEY_PATH.read_bytes()
    return Ed25519PublicKey.from_public_bytes(raw)


def verify_chain(db_path: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT seq, platform, collector_id, collected_at, payload_canonical, "
            "record_hash, entry_hash, prev_entry_hash FROM raw_records ORDER BY seq"
        ).fetchall()

        if not rows:
            return {"status": "PASS", "records": 0, "message": "Empty ledger"}

        prev_hash = "0" * 64
        batch_hashes: list[str] = []
        batch_first = rows[0]["seq"]

        for row in rows:
            payload_bytes = row["payload_canonical"].encode("utf-8")
            expected_record_hash = sha256hex(payload_bytes)
            if expected_record_hash != row["record_hash"]:
                return {
                    "status": "FAIL",
                    "seq": row["seq"],
                    "reason": "record_hash mismatch",
                }

            entry_input = (
                prev_hash.encode()
                + expected_record_hash.encode()
                + row["collected_at"].encode()
                + row["collector_id"].encode()
                + str(row["seq"]).encode()
            )
            expected_entry_hash = sha256hex(entry_input)
            if expected_entry_hash != row["entry_hash"]:
                return {
                    "status": "FAIL",
                    "seq": row["seq"],
                    "reason": "entry_hash chain break",
                }
            if row["prev_entry_hash"] != prev_hash:
                return {
                    "status": "FAIL",
                    "seq": row["seq"],
                    "reason": "prev_entry_hash mismatch",
                }

            prev_hash = row["entry_hash"]
            batch_hashes.append(row["entry_hash"])

        checkpoints = conn.execute(
            "SELECT first_seq, last_seq, merkle_root, signature, pubkey_id FROM ledger_checkpoints ORDER BY first_seq"
        ).fetchall()

        pubkey = load_public_key()
        for cp in checkpoints:
            try:
                sig = base64.b64decode(cp["signature"])
                pubkey.verify(sig, cp["merkle_root"].encode())
            except Exception:
                return {
                    "status": "FAIL",
                    "reason": f"Checkpoint signature invalid for seq {cp['first_seq']}-{cp['last_seq']}",
                }

        return {
            "status": "PASS",
            "records": len(rows),
            "checkpoints": len(checkpoints),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/satya.db")
    args = parser.parse_args()
    result = verify_chain(args.db)
    print(result)
    raise SystemExit(0 if result["status"] == "PASS" else 1)