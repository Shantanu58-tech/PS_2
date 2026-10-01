from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.routers import (
    alerts, cases, collectors, coordination, demographics, eval_router, graph, health, ledger_router,
    lineage, platforms, posts, replay_router, search, situation, stream, timeline, topics, traceability,
)
from app.config import ROOT, settings
from app.db.session import init_db_sync
from app.pipeline import events
from app.version import VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_sync()
    events.bind_loop(asyncio.get_running_loop())
    stop = asyncio.Event()
    task = None
    if settings.mode == "live":
        from app.pipeline.scheduler import live_loop

        task = asyncio.create_task(live_loop(stop))

    async def _warm() -> None:  # build the cached views before the first visitor needs them
        from app.analytics.situation import situation
        from app.api.routers import graph as g, lineage as lin, timeline as tl, topics as tp

        async def flagged_story() -> None:
            # Emotions opens on the flagged story; have its numbers ready (hourly, both views)
            sit = await asyncio.to_thread(situation, settings.db_path)
            tid = ((sit.get("kpis") or {}).get("top_alert") or {}).get("topic_id")
            for t in (tid, None):
                await tl.raw_vs_organic(topic_id=t, platform=None, kind="all")
            if tid is not None:
                for org in (False, True):
                    await tl.emotions_timeline(bucket="1h", topic_id=tid, organic_only=org, platform=None, kind="all")

        steps = [
            lambda: asyncio.to_thread(situation, settings.db_path),
            lambda: tp.list_topics(limit=40, sort="rising"), lambda: tp.list_topics(limit=100, sort="coordinated"),
            lambda: tp.list_topics(limit=8, sort="rising"), lambda: tp.list_topics(limit=30, sort="coordinated"),
            lin.lineage_overview, lambda: g.get_graph(organic_only=False, max_nodes=300),
            lambda: g.get_segment_spread(), lambda: g.get_spread(),
            lambda: g.get_graph(organic_only=True, max_nodes=300),  # the "Organic only" switch
            flagged_story,
        ]
        for step in steps:
            try:
                await step()
            except Exception:  # an empty database has nothing to warm
                pass

    async def _ots_loop() -> None:
        """Bitcoin anchoring in two stages: stamp the newest signed checkpoint on the public
        OpenTimestamps calendars (seconds; one stamp covers every earlier record through the
        chain), then keep asking until the calendars have put it in a Bitcoin block (hours)."""
        from app.ledger.ots import anchor_pending_checkpoints, upgrade_all

        await asyncio.sleep(20)  # let the warm-up go first on a small host
        while not stop.is_set():
            try:
                await asyncio.to_thread(anchor_pending_checkpoints, settings.db_path)
                await asyncio.to_thread(upgrade_all, settings.db_path)
            except Exception:  # offline calendars must never take the API down
                pass
            try:
                await asyncio.wait_for(stop.wait(), timeout=1800)
            except asyncio.TimeoutError:
                pass

    warm = asyncio.create_task(_warm())
    ots = asyncio.create_task(_ots_loop()) if settings.enable_ots else None
    yield
    warm.cancel()
    if ots:
        ots.cancel()
    stop.set()
    if task:
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(title="DEEPASTAMBHA", version=VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Replay/demo is public read-only; live mode should be served same-origin (B5).
    allow_origins=["*"] if settings.mode == "replay" else ["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allowed in the public read-only demo: verification, the tamper simulation (scratch
# copy), case/brief generation, LLM summaries and signal review. Everything else that writes is blocked.
_DEMO_ALLOWED_WRITES = ("/api/ledger/verify", "/api/ledger/tamper-sim", "/api/cases", "/api/summaries/", "/api/alerts/")


@app.middleware("http")
async def demo_readonly_guard(request: Request, call_next):
    if (settings.demo_readonly and request.method not in ("GET", "HEAD", "OPTIONS")
            and not request.url.path.startswith(_DEMO_ALLOWED_WRITES)):
        return JSONResponse({"detail": "Disabled in the public read-only demo."}, status_code=403)
    return await call_next(request)


app.include_router(health.router)
app.include_router(health.router, prefix="/api")
for r in (posts, timeline, topics, graph, coordination, lineage, demographics, alerts, cases,
          ledger_router, stream, collectors, search, eval_router, replay_router, traceability, platforms, situation):
    app.include_router(r.router, prefix="/api")


# B5: serve the built console from the same origin (single URL, no CORS).
_dist = Path(settings.frontend_dist) if settings.frontend_dist else ROOT / "frontend" / "dist"


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    if full_path.startswith(("api/", "healthz")):
        raise HTTPException(404)
    if not _dist.exists():
        raise HTTPException(404, "frontend not built: run `npm run build` in frontend/")
    candidate = (_dist / full_path).resolve()
    if full_path and candidate.is_file() and _dist.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(_dist / "index.html")  # client-side routes (/timeline, /ledger, ...)
