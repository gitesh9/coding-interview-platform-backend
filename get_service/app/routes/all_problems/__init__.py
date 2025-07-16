from fastapi import APIRouter
from .all_problems import router as all_problems_route

all_problems_routes:list[APIRouter] = [
    all_problems_route
]