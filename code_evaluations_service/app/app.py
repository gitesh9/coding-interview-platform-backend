from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from .db.session import Base, engine
from .api.sample_tests import run_sample_code

app = FastAPI()
print("eval Service: ",  os.getenv("CODE_EVAL_SERVICE_URL"))
Base.metadata.create_all(bind=engine)



@app.post("/{problemId}/evaluate")
def eval_code(problemId: str,request: Request):
    print(problemId)
    return JSONResponse(content={"status":"successful","content":"Code Submitted Successfully"},status_code=200)

@app.post("/sample/")
def eval_code_sample(request: Request):
    print(request.body())
    run_sample_code('','')
    return JSONResponse(content={"status":"successful","content":"Code Submitted Successfully"},status_code=200)