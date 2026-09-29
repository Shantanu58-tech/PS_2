from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio, json
from datetime import datetime, timezone

router = APIRouter()


@router.get("/stream")
async def stream():
    async def generator():
        while True:
            data = {"ts": datetime.now(timezone.utc).isoformat(), "type": "heartbeat"}
            yield {"event": "heartbeat", "data": json.dumps(data)}
            await asyncio.sleep(5)
    return EventSourceResponse(generator())
