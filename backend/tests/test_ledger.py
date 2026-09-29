import os, sqlite3, pytest
from hypothesis import given, strategies as st, settings as hsettings


def _tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    from pathlib import Path
    schema = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema.read_text())
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA journal_mode=DELETE")
    return db_path


def test_ledger_chain_and_verify(tmp_path):
    db_path = _tmp_db(tmp_path)
    from app.ledger.chain import LedgerWriter
    from app.ledger.verify import verify_chain
    from datetime import datetime, timezone

    writer = LedgerWriter(db_path)
    with sqlite3.connect(db_path) as conn:
        for i in range(5):
            writer.append(conn, "x", "test", datetime.now(timezone.utc), {"text": f"post {i}", "id": i})
        writer.flush(conn, 5)

    result = verify_chain(db_path)
    assert result["status"] == "PASS", result


def test_tamper_detection(tmp_path):
    db_path = _tmp_db(tmp_path)
    from app.ledger.chain import LedgerWriter
    from app.ledger.verify import verify_chain
    from datetime import datetime, timezone
    import shutil

    writer = LedgerWriter(db_path)
    with sqlite3.connect(db_path) as conn:
        for i in range(10):
            writer.append(conn, "x", "test", datetime.now(timezone.utc), {"text": f"post {i}", "id": i})
        writer.flush(conn, 10)

    scratch = db_path.replace(".db", "_scratch.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    shutil.copy2(db_path, scratch)
    with sqlite3.connect(scratch) as conn:
        conn.execute("DROP TRIGGER IF EXISTS raw_no_update")
        conn.execute("UPDATE raw_records SET payload_canonical='tampered' WHERE seq=3")
        conn.commit()

    result = verify_chain(scratch)
    assert result["status"] == "FAIL"
    try:
        os.remove(scratch)
    except OSError:
        pass


@given(st.binary(min_size=1, max_size=100))
@hsettings(max_examples=50)
def test_canonical_json_deterministic(b):
    from app.ledger.canonical import canonical_json
    import json
    obj = {"data": b.hex(), "n": len(b)}
    assert canonical_json(obj) == canonical_json(obj)


def test_merkle_root_changes_on_tamper():
    from app.ledger.merkle import build_merkle_root
    hashes = ["aa" * 32, "bb" * 32, "cc" * 32, "dd" * 32]
    root1 = build_merkle_root(hashes)
    hashes2 = list(hashes)
    hashes2[1] = "ee" * 32
    root2 = build_merkle_root(hashes2)
    assert root1 != root2


def test_k_anonymity_suppression():
    counts = {"delhi": 5, "mumbai": 15, "bengaluru": 3}
    k = 10
    suppressed = {b: c if c >= k else "suppressed" for b, c in counts.items()}
    assert suppressed["delhi"] == "suppressed"
    assert suppressed["mumbai"] == 15
    assert suppressed["bengaluru"] == "suppressed"


def test_no_per_account_demographics_endpoint():
    from pathlib import Path
    router_dir = Path(__file__).parent.parent / "app" / "api" / "routers"
    for router_file in router_dir.glob("*.py"):
        content = router_file.read_text()
        assert "per_account" not in content.lower() or "no per-account" in content.lower()
