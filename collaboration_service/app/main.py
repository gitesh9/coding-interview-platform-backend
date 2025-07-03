import os, uvicorn

if __name__=="__main__":
    port = int(os.environ.get("PORT",8004))
    uvicorn.run("app:app",host="0.0.0.0",port=port, reload=True)