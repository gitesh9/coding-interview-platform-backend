import uvicorn, os
if __name__=="__main__":
    print("brussah: ",os.getenv("CODE_EVAL_SERVICE_URL"))
    port  = int(os.environ.get("PORT",8003))
    uvicorn.run("app:app", host="0.0.0.0",port=port, reload=True)