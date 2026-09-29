from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.routers import (
    alerts, cases, collectors, coordination, demographics, eval_router, graph, health, ledger_router,
    lineage, posts, replay_router, search, stream, timeline, topics, traceability,
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
    yield
    stop.set()
    if task:
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(title="SATYA-NET", version=VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Replay/demo is public read-only; live mode should be served same-origin (B5).
    allow_origins=["*"] if settings.mode == "replay" else ["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(health.router, prefix="/api")
for r in (posts, timeline, topics, graph, coordination, lineage, demographics, alerts, cases,
          ledger_router, stream, collectors, search, eval_router, replay_router, traceability):
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
