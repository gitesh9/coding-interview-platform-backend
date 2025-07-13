from fastapi import APIRouter
from .problem import problem_routes
from .all_problems import all_problems_routes
from .user import user_routes

all_routes:list[list[APIRouter]] = [
    problem_routes,
    user_routes,
    all_problems_routes
]