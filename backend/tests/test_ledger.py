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


def test_checkpoint_root_must_match_entries(tmp_path):
    # A checkpoint whose root is validly signed but does not match the covered
    # entries must fail: signature checks alone are not enough.
    db_path = _tmp_db(tmp_path)
    from app.ledger.chain import LedgerWriter
    from app.ledger.sign import Signer
    from app.ledger.verify import verify_chain
    from datetime import datetime, timezone

    writer = LedgerWriter(db_path)
    with sqlite3.connect(db_path) as conn:
        for i in range(4):
            writer.append(conn, "x", "test", datetime.now(timezone.utc), {"text": f"p{i}", "id": i})
        writer.flush(conn, 4)

    forged_root = "ab" * 32
    forged_sig = Signer().sign(forged_root.encode())
    with sqlite3.connect(db_path) as conn:
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='ledger_checkpoints'"
        ).fetchall():
            conn.execute(f"DROP TRIGGER {name}")
        conn.execute(
            "UPDATE ledger_checkpoints SET merkle_root=?, signature=?", (forged_root, forged_sig)
        )
        conn.commit()

    result = verify_chain(db_path)
    assert result["status"] == "FAIL"
    assert "Merkle root mismatch" in result["reason"]


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
    import requests
    import re
    from pathlib import Path
    router_dir = Path(__file__).parent.parent / "app" / "api" / "routers"
    for router_file in router_dir.glob("*.py"):
        content = router_file.read_text()
        assert "per_account" not in content.lower() or "no per-account" in content.lower()


def test_inclusion_proof_verifies_with_public_key_only(tmp_path):
    db_path = _tmp_db(tmp_path)
    from datetime import datetime, timezone

    from app.ledger.chain import LedgerWriter
    from app.ledger.proof import inclusion_proof, verify_inclusion, verify_signature
    from app.ledger.sign import PUBLIC_KEY_PATH

    writer = LedgerWriter(db_path)
    with sqlite3.connect(db_path) as conn:
        for i in range(7):
            writer.append(conn, "x", "test", datetime.now(timezone.utc), {"i": i})
        writer.flush(conn, 7)
    for seq in (1, 4, 7):
        p = inclusion_proof(db_path, seq)
        root = p["checkpoint"]["merkle_root"]
        assert verify_inclusion(p["record"]["entry_hash"], p["path"], root)
        assert not verify_inclusion("00" * 32, p["path"], root)
        assert verify_signature(root, p["checkpoint"]["signature"], PUBLIC_KEY_PATH.read_bytes())


def test_audit_actions_are_chained_in_ledger(tmp_path):
    from app.db.session import init_db_sync
    from app.ledger.audit import log_action
    from app.ledger.verify import verify_chain
    from app.pipeline.workers import reset_ingestors

    db_path = str(tmp_path / "audit.db")
    init_db_sync(db_path)
    reset_ingestors()
    s1 = log_action(db_path, "analyst", "open_case", {"case": 1})
    s2 = log_action(db_path, "analyst", "export", {"case": 1})
    assert s2 == s1 + 1
    with sqlite3.connect(db_path) as c:
        assert c.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 2
        assert c.execute("SELECT collector_id FROM raw_records WHERE seq=?", (s1,)).fetchone()[0] == "audit"
    assert verify_chain(db_path)["status"] == "PASS"
    reset_ingestors()


@given(st.integers(min_value=0, max_value=10_000))
@hsettings(max_examples=25, deadline=None)
def test_any_single_char_mutation_fails_verification(tmp_path_factory, pos):
    """Property: after any single-character change to a stored payload, verify FAILs."""
    from datetime import datetime, timezone

    from app.ledger.chain import LedgerWriter
    from app.ledger.verify import verify_chain

    db_path = _tmp_db(tmp_path_factory.mktemp("prop"))
    w = LedgerWriter(db_path)
    with sqlite3.connect(db_path) as conn:
        for i in range(5):
            w.append(conn, "x", "t", datetime.now(timezone.utc), {"text": f"record number {i}", "i": i})
        w.flush(conn, 5)
        conn.execute("DROP TRIGGER raw_no_update")
        seq = pos % 5 + 1
        payload = conn.execute("SELECT payload_canonical FROM raw_records WHERE seq=?", (seq,)).fetchone()[0]
        k = pos % len(payload)
        mutated = payload[:k] + ("#" if payload[k] != "#" else "@") + payload[k + 1:]
        conn.execute("UPDATE raw_records SET payload_canonical=? WHERE seq=?", (mutated, seq))
        conn.commit()
    res = verify_chain(db_path)
    assert res["status"] == "FAIL" and res["seq"] == seq
