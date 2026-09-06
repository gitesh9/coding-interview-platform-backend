from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Routes import routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://interviewpracticeplatform.netlify.app","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)