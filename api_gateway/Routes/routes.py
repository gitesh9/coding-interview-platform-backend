from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import os, httpx, websockets, asyncio

AUTH_SERVICE = os.getenv("AUTH_SERVICE", "http://auth_service:8001")
GET_SERVICE = os.getenv("GET_SERVICE", "http://get_service:8002")
CODE_EVALUATION_SERVICE = os.getenv("CODE_EVALUATIONS_SERVICE", "http://code_evaluations_service:8003")
COLLABORATION_SERVICE = os.getenv("COLLABORATION_SERVICE", "http://collaboration_service:8004")
INTERVIEW_SERVICE = os.getenv("INTERVIEW_SERVICE", "http://interview_service:8005")

router = APIRouter()

# ─── Auth proxy ──────────────────────────────────────────────────────────────

@router.api_route("/auth/{path:path}", methods=["GET", "POST"])
async def proxy_auth(path: str, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{AUTH_SERVICE}/{path}",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

# ─── Get service proxy ───────────────────────────────────────────────────────

@router.api_route("/get/{path:path}", methods=["GET"])
async def proxy_get(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        try:
            url = f"{GET_SERVICE}/{path}"
            if request.query_params:
                url += f"?{request.query_params}"
            response = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

# ─── Code execution proxy ────────────────────────────────────────────────────

@router.api_route("/problems/{problemId}/run", methods=["POST"])
async def proxy_run(problemId: str, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{CODE_EVALUATION_SERVICE}/{problemId}/sample",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)


@router.api_route("/problems/{problemId}/submit", methods=["POST"])
async def proxy_submit(problemId: str, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{CODE_EVALUATION_SERVICE}/{problemId}/evaluate",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
                timeout=30.0,
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

# ─── Interview sessions proxy ────────────────────────────────────────────────

@router.api_route("/interviews/sessions", methods=["GET", "POST"])
async def proxy_sessions(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            url = f"{INTERVIEW_SERVICE}/sessions"
            if request.query_params:
                url += f"?{request.query_params}"
            response = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)


@router.api_route("/interviews/sessions/join", methods=["POST"])
async def proxy_session_join(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method="POST",
                url=f"{INTERVIEW_SERVICE}/sessions/join",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)


@router.api_route("/interviews/sessions/{sessionId}/end", methods=["PATCH"])
async def proxy_session_end(sessionId: str, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method="PATCH",
                url=f"{INTERVIEW_SERVICE}/sessions/{sessionId}/end",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body,
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)


@router.api_route("/interviews/sessions/{sessionId}", methods=["GET"])
async def proxy_session_detail(sessionId: str, request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method="GET",
                url=f"{INTERVIEW_SERVICE}/sessions/{sessionId}",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

# ─── Collaboration proxy ─────────────────────────────────────────────────────

@router.api_route("/collab/", methods=["POST"])
async def proxy_collab(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{COLLABORATION_SERVICE}/create_session",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        except httpx.RequestError as e:
            return JSONResponse(status_code=502, content={"error": "Gateway request failed", "detail": str(e)})

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)


@router.websocket("/collab/{sessionId}")
async def proxy_collab_ws(websocket: WebSocket, sessionId: str):
    await websocket.accept()
    userId = websocket.query_params.get("userId", "")
    ws_url = COLLABORATION_SERVICE.replace("http", "ws")
    try:
        async with websockets.connect(f"{ws_url}/ws/{sessionId}?userId={userId}") as backend_ws:
            async def forward_to_backend():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except WebSocketDisconnect:
                    pass

            async def forward_to_client():
                try:
                    async for message in backend_ws:
                        await websocket.send_text(message)
                except Exception:
                    pass

            await asyncio.gather(forward_to_backend(), forward_to_client())
    except Exception:
        await websocket.close()










