from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/create_session")
def create_session(request: Request):
    return JSONResponse(content={"status":"successful","content":"Session Created Successfully"},status_code=200)