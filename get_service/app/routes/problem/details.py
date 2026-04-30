from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from fastapi import Depends
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db.models.models import Problem, UserProblemStatus, UserProblemStatusEnum
from ...db.schemas.schemas import (
    ProblemDetailSchema,
    ExampleSchema,
    TestCaseSchema,
    SimilarProblemResponseSchema,
)
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Union
from .similar_problems import vector_store
import os
import jwt
import json

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def _get_user_id(authorization: str) -> Optional[int]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except Exception:
        return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router: APIRouter = APIRouter()

def _to_frontend_problem(problem: Problem, is_solved: Optional[bool] = None) -> dict:
    """Convert a DB Problem row to the frontend Problem interface shape."""
    # Map sample_testcases → examples
    examples = [
        {"input": tc.input_data, "output": tc.expected_output, "explanation": tc.explanation}
        for tc in (problem.sample_testcases or [])
    ]

    # Map sample_testcases → testCases (frontend TestCase shape)
    test_cases = [
        {"id": tc.id, "input": tc.input_data, "expectedOutput": tc.expected_output}
        for tc in (problem.sample_testcases or [])
    ]

    # constraints: stored as a single string, split into list
    constraints_list = []
    if problem.constraints:
        constraints_list = [c.strip() for c in problem.constraints.split("\n") if c.strip()]

    # starterCode: code_templates JSONB → dict
    starter_code = {}
    if problem.code_templates:
        if isinstance(problem.code_templates, str):
            starter_code = json.loads(problem.code_templates)
        else:
            starter_code = problem.code_templates

    # Capitalize difficulty to match frontend ('Easy', 'Medium', 'Hard')
    difficulty = problem.difficulty.value if hasattr(problem.difficulty, 'value') else str(problem.difficulty)
    difficulty = difficulty.capitalize()

    return {
        "id": problem.id,
        "title": problem.title,
        "difficulty": difficulty,
        "description": problem.description,
        "examples": examples,
        "constraints": constraints_list,
        "starterCode": starter_code,
        "testCases": test_cases,
        "isSolved": is_solved,
    }


@router.get('/problems/{value}')
def get_problem_details(
    value: str,
    db: Session = Depends(get_db),
    authorization: str = Header(default=""),
):
    query = db.query(Problem)
    if value.isdigit():
        problem_data = query.filter(Problem.id == int(value)).first()
    else:
        problem_data = query.filter(Problem.slug.ilike(value)).first()

    if not problem_data:
        return JSONResponse(
            status_code=404,
            content={"error": 404, "message": "Problem not found"}
        )

    is_solved = None
    user_id = _get_user_id(authorization)
    if user_id is not None:
        status_row = (
            db.query(UserProblemStatus)
            .filter(
                UserProblemStatus.user_id == user_id,
                UserProblemStatus.problem_id == problem_data.id,
                UserProblemStatus.status == UserProblemStatusEnum.solved,
            )
            .first()
        )
        is_solved = status_row is not None

    return _to_frontend_problem(problem_data, is_solved=is_solved)