from fastapi import APIRouter
from .user_details import router as user_info

user_routes: list[APIRouter] = [
    user_info
]