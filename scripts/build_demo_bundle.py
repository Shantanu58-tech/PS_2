"""Build the hosted demo bundle from scratch, with the incident in the most recent week.

    backend\\.venv\\Scripts\\python scripts\\build_demo_bundle.py --keys <dir with ledger_ed25519(.pub)> --out <dir>

Steps: generate the scenario (seed 7) anchored to now -> Instagram/Facebook export
sample anchored the same way -> replay everything through the ledger -> run every
analytics stage -> verify the ledger -> pack data/deepastambha.db + ledger keys +
the synthetic meme images into bundle.tar.gz. Upload the tarball to the private
dataset named in deploy/render/start.sh (BUNDLE_REPO) and restart the service.
Re-run it shortly before a demo so the "last 7 days" really are the last 7 days.
"""
from __future__ import annotations

import argparse
import gc
import os
import shutil
import sqlite3
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scenario"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True, help="directory holding ledger_ed25519 and ledger_ed25519.pub")
    ap.add_argument("--out", required=True, help="work/output directory")
    ap.add_argument("--anchor", default="now")
    ap.add_argument("--pack-only", action="store_true", help="skip the build; only compact and pack an existing work dir")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    work = out / "data"
    if a.pack_only:
        os.environ.update(DB_PATH=str(work / "deepastambha.db"), KEYS_DIR=str(work / "keys"))
        stamp_bitcoin(str(work / "deepastambha.db"))  # no-op when the newest checkpoint is already stamped
        pack(out, work, time.time())
        return
    shutil.rmtree(out, ignore_errors=True)
    (work / "keys").mkdir(parents=True)
    for f in ("ledger_ed25519", "ledger_ed25519.pub"):
        shutil.copy(Path(a.keys) / f, work / "keys" / f)
    os.environ.update(DB_PATH=str(work / "deepastambha.db"), KEYS_DIR=str(work / "keys"),
                      MEDIA_DIR=str(work / "media"), ENABLE_OTS="false", AUTO_ANALYTICS="false")

    from app.config import settings
    from app.db.session import init_db_sync
    from app.collectors.replay import run_replay_sync
    from app.collectors.import_csv import read_csv
    from app.pipeline.workers import get_ingestor
    from app.pipeline.analytics import run_all_analytics
    from app.ledger.verify import verify_chain
    from scenario.generate import generate_scenario
    import meta_export_sample as meta

    anchor = datetime.now(timezone.utc) if a.anchor == "now" else datetime.fromisoformat(a.anchor)
    t = time.time()
    scen = out / "scenario_v1.jsonl"
    generate_scenario(7, str(scen), str(work / "media"), anchor=anchor)
    meta.set_anchor(anchor)
    import random
    rng = random.Random(7)
    meta.write(meta.instagram(rng), out / "instagram_export_sample.csv")
    meta.write(meta.facebook(rng), out / "facebook_export_sample.csv")

    init_db_sync(settings.db_path)
    n = run_replay_sync(str(scen), settings.db_path, analytics=False)
    for plat in ("instagram", "facebook"):
        n += get_ingestor().ingest_many(read_csv(out / f"{plat}_export_sample.csv", plat))
    print(f"ingested {n} records in {time.time() - t:.0f}s", flush=True)
    report = run_all_analytics(settings.db_path)
    print({k: v["seconds"] for k, v in report.items()}, flush=True)
    result = verify_chain(settings.db_path)
    print("verify:", result, flush=True)
    assert result.get("status") == "PASS"
    stamp_bitcoin(settings.db_path)

    pack(out, work, t)


def stamp_bitcoin(db_path: str) -> None:
    """Submit the newest checkpoint to the public OpenTimestamps calendars (pending proof);
    the server later upgrades it to the Bitcoin block that confirms it."""
    from app.config import settings
    from app.ledger.ots import anchor_pending_checkpoints

    settings.enable_ots = True
    print("bitcoin anchor:", anchor_pending_checkpoints(db_path), flush=True)


def pack(out: Path, work: Path, t: float) -> None:
    from app.pipeline.workers import reset_ingestors

    # `with sqlite3.connect()` only commits; drop every lingering handle before switching journal mode
    reset_ingestors()
    gc.collect()
    c = sqlite3.connect(work / "deepastambha.db", isolation_level=None)
    try:
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        c.execute("PRAGMA journal_mode=DELETE")
        c.execute("VACUUM")
    finally:
        c.close()
    with tarfile.open(out / "bundle.tar.gz", "w:gz") as tar:
        tar.add(work / "deepastambha.db", arcname="data/deepastambha.db")
        for f in ("ledger_ed25519", "ledger_ed25519.pub"):
            tar.add(work / "keys" / f, arcname=f"data/keys/{f}")
        for img in sorted((work / "media").glob("*")):
            tar.add(img, arcname=f"data/media/{img.name}")
    print(f"bundle ready: {out / 'bundle.tar.gz'} ({(out / 'bundle.tar.gz').stat().st_size / 1e6:.1f} MB) "
          f"in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
