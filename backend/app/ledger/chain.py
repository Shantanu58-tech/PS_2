from __future__ import annotations
import hashlib
import sqlite3
from datetime import datetime, timezone
from app.ledger.canonical import canonical_json
from app.ledger.merkle import build_merkle_root
from app.ledger.sign import Signer


GENESIS_HASH = "0" * 64


def sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LedgerWriter:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._signer = Signer()
        self._prev_hash = self._load_last_hash()
        self._batch: list[str] = []
        self._batch_first_seq: int | None = None
        self._batch_size = 100

    def _load_last_hash(self) -> str:
        try:
            with sqlite3.connect(self._db_path) as conn:
                row = conn.execute(
                    "SELECT entry_hash FROM raw_records ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                return row[0] if row else GENESIS_HASH
        except Exception:
            return GENESIS_HASH

    def append(
        self,
        db: sqlite3.Connection,
        platform: str,
        collector_id: str,
        collected_at: datetime,
        payload: dict,
    ) -> int:
        payload_bytes = canonical_json(payload)
        record_hash = sha256hex(payload_bytes)
        ts_str = collected_at.isoformat()
        # Pre-compute the next seq so we can include it in entry_hash
        # without needing a forbidden UPDATE after INSERT.
        row = db.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM raw_records"
        ).fetchone()
        seq = row[0]
        entry_input = (
            self._prev_hash.encode()
            + record_hash.encode()
            + ts_str.encode()
            + collector_id.encode()
            + str(seq).encode()
        )
        entry_hash = sha256hex(entry_input)
        db.execute(
            """
            INSERT INTO raw_records
            (platform, collector_id, collected_at, payload_canonical, record_hash, entry_hash, prev_entry_hash)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                platform, collector_id, ts_str,
                payload_bytes.decode("utf-8"),
                record_hash, entry_hash, self._prev_hash,
            ),
        )
        db.commit()
        self._prev_hash = entry_hash
        self._batch.append(entry_hash)
        if self._batch_first_seq is None:
            self._batch_first_seq = seq
        if len(self._batch) >= self._batch_size:
            self._flush_checkpoint(db, seq)
        return seq

    def _flush_checkpoint(self, db: sqlite3.Connection, last_seq: int) -> None:
        if not self._batch:
            return
        root = build_merkle_root(self._batch)
        sig = self._signer.sign(root.encode())
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            """
            INSERT INTO ledger_checkpoints
            (first_seq, last_seq, merkle_root, signature, pubkey_id, created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (self._batch_first_seq, last_seq, root, sig, self._signer.pubkey_id, now),
        )
        db.commit()
        self._batch = []
        self._batch_first_seq = None

    def flush(self, db: sqlite3.Connection, last_seq: int) -> None:
        self._flush_checkpoint(db, last_seq)
