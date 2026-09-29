import asyncio
import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.pipeline import events

router = APIRouter()


@router.get("/stream")
async def stream(request: Request):
    """SSE: replay/analytics progress, stage completions, alert updates, heartbeats."""
    queue = events.subscribe()

    async def generator():
        try:
            yield {"event": "status", "data": json.dumps(events.status)}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield {"event": event["type"], "data": json.dumps(event, default=str)}
                except asyncio.TimeoutError:
                    yield {"event": "heartbeat", "data": "{}"}
        finally:
            events.unsubscribe(queue)

    return EventSourceResponse(generator())
