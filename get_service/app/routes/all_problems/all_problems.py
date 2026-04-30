from fastapi import APIRouter, Query, Header
from fastapi import Depends
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db.models.models import Problem, UserProblemStatus, UserProblemStatusEnum
from ...db.schemas.schemas import ProblemListItemSchema
from typing import List, Optional, Set
import os
import jwt
import weaviate
from weaviate.classes.query import MetadataQuery
from weaviate.classes.config import Property, Configure, DataType, Integrations

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


def _get_solved_problem_ids(db: Session, user_id: int) -> Set[int]:
    rows = (
        db.query(UserProblemStatus.problem_id)
        .filter(
            UserProblemStatus.user_id == user_id,
            UserProblemStatus.status == UserProblemStatusEnum.solved,
        )
        .all()
    )
    return {r[0] for r in rows}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router: APIRouter = APIRouter()

def _to_list_item(p: Problem, solved_ids: Set[int]) -> dict:
    difficulty = p.difficulty.value if hasattr(p.difficulty, 'value') else str(p.difficulty)
    return {
        "id": p.id,
        "slug": p.slug,
        "title": p.title,
        "difficulty": difficulty.capitalize(),
        "tags": p.tags,
        "constraints": p.constraints,
        "description": p.description,
        "isSolved": p.id in solved_ids,
    }

@router.get('/problems-set/')
def get_all_problems(
    db: Session = Depends(get_db),
    authorization: str = Header(default=""),
):
    user_id = _get_user_id(authorization)
    solved_ids = _get_solved_problem_ids(db, user_id) if user_id else set()
    problems = db.query(Problem).all()
    return [_to_list_item(p, solved_ids) for p in problems]


@router.get('/problems')
def get_search_query(
    value: str = Query(..., description="Search query string"),
    db: Session = Depends(get_db),
):

    # ✅ Initialize Weaviate v4 client
    client = weaviate.connect_to_local(
            port=8002,
    )
    client.integrations.configure([
        Integrations.openai(api_key="...")
    ])

    # ✅ Ensure collection exists
    if not client.collections.exists("Problem"):
        client.collections.create(
            name="Problem",
            description="Problem-related data",
            vectorizer_config=[Configure.NamedVectors.text2vec_openai(name="openaiFirst")],
            properties=[
                Property(name="title", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="difficulty", data_type=DataType.TEXT),
                Property(name="tags", data_type=DataType.TEXT),
                Property(name="constraints", data_type=DataType.TEXT),
                Property(name="hints", data_type=DataType.TEXT),
                Property(name="sample_testcases", data_type=DataType.TEXT),
                Property(name="discussions", data_type=DataType.TEXT),
                Property(name="submissions", data_type=DataType.TEXT),
                Property(name="user_statuses", data_type=DataType.TEXT)
            ]
        )

    # ✅ Perform semantic search using `near_text`
    results = client.collections.get("Problem").query.near_text(
        query=value,
        limit=5,
        return_metadata=MetadataQuery(distance=True),
        return_properties=[
            "title", "description", "difficulty", "tags", "constraints"
        ]
    )

    # ✅ Convert Weaviate results to ProblemListItem format
    problems = []
    for obj in results.objects:
        props = obj.properties
        difficulty = str(props.get("difficulty", "")).capitalize()
        problems.append({
            "id": 0,
            "slug": "",
            "title": str(props.get("title", "")),
            "difficulty": difficulty,
            "tags": str(props.get("tags", "")),
            "constraints": str(props.get("constraints", "")),
            "description": str(props.get("description", "")),
            "isSolved": None,
        })

    return problems