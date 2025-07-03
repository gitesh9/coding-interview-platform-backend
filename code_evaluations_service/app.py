from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/{problemId}/evaluate")
def eval_code(problemId: str,request: Request):
    print(problemId)
    return JSONResponse(content={"status":"successful","content":"Code Submitted Successfully"},status_code=200)