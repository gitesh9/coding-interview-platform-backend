from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os, httpx

AUTH_SERVICE = os.getenv("AUTH_SERVICE", "http://auth_service:8001")
GET_SERVICE = os.getenv("GET_SERVICE", "http://get_service:8002")
CODE_EVALUATION_SERVICE = os.getenv("CODE_EVALUATIONS_SERVICE", "http://code_evaluations_service:8003")
COLLABORATION_SERVICE = os.getenv("COLLABORATION_SERVICE", "http://collaboration_service:8004")

router = APIRouter()

# @router.api_route("/auth/{path:path}",methods=["GET","POST"])
# async def proxy_auth(path:str,request: Request):
#     async with httpx.AsyncClient() as client:
#         response = await client.request(
#             method=request.method,
#             url=f"{AUTH_SERVICE}/{path}",
#             headers= dict(request.headers.raw),
#             content= await request.body()
#         )
#     return response.json()

@router.api_route("/get/{path:path}",methods=["GET"])
async def proxy_get(path:str, request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{GET_SERVICE}/{path}",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"}
            )
        except httpx.RequestError as e:
             return JSONResponse(
                status_code=502,
                content={"error": "Gateway request failed", "detail": str(e)}
            )

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

@router.api_route("/problems/{problemId}/run",methods=["POST"])
async def proxy_run(problemId: str, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{CODE_EVALUATION_SERVICE}/{problemId}/sample",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body
            )
        except httpx.RequestError as e:
             return JSONResponse(
                status_code=502,
                content={"error": "Gateway request failed", "detail": str(e)}
            )
    print("shalalala: ",response)
    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

@router.api_route("/problems/{problemId}/submit",methods=["POST"])
async def proxy_submit(problemId: str, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{CODE_EVALUATION_SERVICE}/{problemId}/evaluate",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body
            )
        except httpx.RequestError as e:
             return JSONResponse(
                status_code=502,
                content={"error": "Gateway request failed", "detail": str(e)}
            )

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)

@router.api_route("/collab/",methods=["POST"])
async def proxy_collab(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{COLLABORATION_SERVICE}/create_session",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"}
            )
        except httpx.RequestError as e:
             return JSONResponse(
                status_code=502,
                content={"error": "Gateway request failed", "detail": str(e)}
            )

    try:
        content = response.json()
    except Exception:
        content = {"error": "Non-JSON response", "raw": response.text}

    return JSONResponse(status_code=response.status_code, content=content)










