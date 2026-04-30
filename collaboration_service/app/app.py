from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, Set
import json
import uuid

app = FastAPI()

# In-memory session store: session_id -> set of connected WebSockets
sessions: Dict[str, Set[WebSocket]] = {}


@app.post("/create_session")
def create_session(request: Request):
    session_id = str(uuid.uuid4())
    sessions[session_id] = set()
    return JSONResponse(
        content={"status": "successful", "sessionId": session_id},
        status_code=200,
    )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    user_id = websocket.query_params.get("userId", "anonymous")

    if session_id not in sessions:
        sessions[session_id] = set()
    sessions[session_id].add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to all other participants in the same session
            for peer in list(sessions.get(session_id, [])):
                if peer != websocket:
                    try:
                        await peer.send_text(data)
                    except Exception:
                        sessions[session_id].discard(peer)
    except WebSocketDisconnect:
        sessions.get(session_id, set()).discard(websocket)
        if session_id in sessions and len(sessions[session_id]) == 0:
            del sessions[session_id]