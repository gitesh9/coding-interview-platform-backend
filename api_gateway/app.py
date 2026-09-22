import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Routes import routes

DEFAULT_ALLOWED_ORIGINS = "https://interviewpracticeplatform.netlify.app,http://localhost:4200"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)