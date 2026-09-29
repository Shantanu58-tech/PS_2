from pathlib import Path


def test_schema_sql_exists():
    schema = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    assert schema.exists()
    content = schema.read_text()
    assert "raw_records" in content
    assert "ledger_checkpoints" in content
    assert "posts" in content


def test_config_loads():
    from app.config import settings
    assert settings.k_anon == 10
    assert settings.mode in ("replay", "live")


def test_canonical_json_deterministic():
    from app.ledger.canonical import canonical_json
    obj = {"z": 1, "a": 2, "m": [3, 4]}
    assert canonical_json(obj) == canonical_json(obj)
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


def test_db_init_creates_tables(tmp_path):
    import sqlite3
    schema = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    db_path = str(tmp_path / "test.db")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema.read_text())
    with sqlite3.connect(db_path) as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert "raw_records" in tables
    assert "posts" in tables
    assert "ledger_checkpoints" in tables
    assert "coord_clusters" in tables
    assert "demo_aggregates" in tables


def test_no_per_account_demographic_endpoint():
    src_dir = Path(__file__).parent.parent / "app" / "api" / "routers"
    for f in src_dir.glob("*.py"):
        text = f.read_text(encoding="utf-8")
        assert "per_account_demographics" not in text
        assert "individual_demographic" not in text
