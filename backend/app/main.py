from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.session import init_db_sync
from app.api.routers import (
    health, posts, timeline, topics, graph, coordination,
    lineage, demographics, alerts, cases, ledger_router,
    stream, collectors, search, eval_router, replay_router, traceability,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_sync()
    yield


app = FastAPI(title="SATYA-NET", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(posts.router, prefix="/api")
app.include_router(timeline.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(coordination.router, prefix="/api")
app.include_router(lineage.router, prefix="/api")
app.include_router(demographics.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(ledger_router.router, prefix="/api")
app.include_router(stream.router, prefix="/api")
app.include_router(collectors.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(eval_router.router, prefix="/api")
app.include_router(replay_router.router, prefix="/api")
app.include_router(traceability.router, prefix="/api")

frontend_dist = Path("../frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
