import aiosqlite
import sqlite3
from pathlib import Path
from app.config import settings


def get_db_path() -> str:
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def init_db_sync() -> None:
    schema = Path(__file__).parent / "schema.sql"
    with sqlite3.connect(get_db_path()) as conn:
        conn.executescript(schema.read_text())


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db
