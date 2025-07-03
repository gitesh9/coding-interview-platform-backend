from fastapi import APIRouter
from .details import router as problem_details_route

problem_routes:list[APIRouter] = [
    problem_details_route
]