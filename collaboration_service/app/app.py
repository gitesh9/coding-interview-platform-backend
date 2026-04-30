import asyncio
import os
import uuid
from typing import Dict, Set, Tuple

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import redis.asyncio as redis

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CHANNEL_PREFIX = "collab:session:"
SESSION_KEY_PREFIX = "collab:exists:"

# Per-process map: session_id -> set of (sender_id, websocket) tuples.
# sender_id is a UUID generated per WebSocket connection so the fanout
# listener can skip echoing a message back to the originating socket.
local_connections: Dict[str, Set[Tuple[str, WebSocket]]] = {}

_redis_client: "redis.Redis | None" = None


async def get_redis() -> "redis.Redis":
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


@app.on_event("shutdown")
async def shutdown():
    if _redis_client is not None:
        await _redis_client.aclose()


@app.post("/create_session")
async def create_session(request: Request):
    session_id = str(uuid.uuid4())
    r = await get_redis()
    # Mark session as existing for 24h (TTL refreshes on connect implicitly via channel use)
    await r.set(f"{SESSION_KEY_PREFIX}{session_id}", "1", ex=86400)
    return JSONResponse(
        content={"status": "successful", "sessionId": session_id},
        status_code=200,
    )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    sender_id = str(uuid.uuid4())
    entry: Tuple[str, WebSocket] = (sender_id, websocket)

    local_connections.setdefault(session_id, set()).add(entry)

    r = await get_redis()
    pubsub = r.pubsub()
    channel = f"{CHANNEL_PREFIX}{session_id}"
    await pubsub.subscribe(channel)

    async def fanout_from_redis():
        """Forward Redis messages to all local sockets except the original sender."""
        try:
            async for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                raw = msg.get("data")
                if not raw or "|" not in raw:
                    continue
                origin_id, payload = raw.split("|", 1)
                for peer_id, peer_ws in list(local_connections.get(session_id, set())):
                    if peer_id == origin_id:
                        continue  # don't echo back to sender
                    try:
                        await peer_ws.send_text(payload)
                    except Exception:
                        local_connections.get(session_id, set()).discard((peer_id, peer_ws))
        except asyncio.CancelledError:
            return
        except Exception:
            return

    fanout_task = asyncio.create_task(fanout_from_redis())

    try:
        while True:
            data = await websocket.receive_text()
            # Prefix with sender_id so the fanout listener can suppress echo.
            await r.publish(channel, f"{sender_id}|{data}")
    except WebSocketDisconnect:
        pass
    finally:
        fanout_task.cancel()
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            pass
        local_connections.get(session_id, set()).discard(entry)
        if session_id in local_connections and not local_connections[session_id]:
            del local_connections[session_id]
