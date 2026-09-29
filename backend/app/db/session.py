import aiosqlite
import sqlite3
from pathlib import Path
from app.config import settings

# Columns added after the first schema release: (table, column, DDL type).
_MIGRATIONS = [
    ("topics", "nature", "TEXT DEFAULT 'organic'"),
    ("topics", "coordinated_share", "REAL DEFAULT 0"),
    ("coord_clusters", "regular_share", "REAL"),
    ("coord_clusters", "basis", "TEXT"),
    ("ledger_checkpoints", "ots_status", "TEXT"),
    ("ledger_checkpoints", "ots_block", "INTEGER"),
]


def get_db_path() -> str:
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def init_db_sync(db_path: str | None = None) -> None:
    schema = Path(__file__).parent / "schema.sql"
    path = db_path or get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(schema.read_text())
        for table, column, ddl in _MIGRATIONS:
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        conn.commit()


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db
