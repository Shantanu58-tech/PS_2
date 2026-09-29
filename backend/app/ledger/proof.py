"""Merkle inclusion proofs: a verifier needs only the record, the proof and
the ledger public key (PRD section 9.1)."""
from __future__ import annotations

import base64
import hashlib
import sqlite3

from app.ledger.merkle import merkle_proof


def inclusion_proof(db_path: str, seq: int) -> dict | None:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cp = conn.execute(
            "SELECT id, first_seq, last_seq, merkle_root, signature, pubkey_id FROM ledger_checkpoints "
            "WHERE first_seq <= ? AND last_seq >= ?", (seq, seq)).fetchone()
        if not cp:
            return None
        hashes = [r[0] for r in conn.execute(
            "SELECT entry_hash FROM raw_records WHERE seq BETWEEN ? AND ? ORDER BY seq",
            (cp["first_seq"], cp["last_seq"]))]
        rec = conn.execute(
            "SELECT seq, record_hash, entry_hash, prev_entry_hash, collected_at, collector_id "
            "FROM raw_records WHERE seq=?", (seq,)).fetchone()
    return {
        "record": dict(rec),
        "checkpoint": dict(cp),
        "index": seq - cp["first_seq"],
        "path": merkle_proof(hashes, seq - cp["first_seq"]),
    }


def verify_inclusion(entry_hash: str, path: list[dict], merkle_root: str) -> bool:
    h = bytes.fromhex(entry_hash)
    for step in path:
        sib = bytes.fromhex(step["hash"])
        h = hashlib.sha256(h + sib if step["position"] == "right" else sib + h).digest()
    return h.hex() == merkle_root


def verify_signature(merkle_root: str, signature_b64: str, public_key_raw: bytes) -> bool:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        Ed25519PublicKey.from_public_bytes(public_key_raw).verify(
            base64.b64decode(signature_b64), merkle_root.encode())
        return True
    except Exception:
        return False
