from fastapi import APIRouter, Query
from fastapi import Depends
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db.models.models import Problem
from ...db.schemas.schemas import ProblemResponseSchema
from typing import List
import weaviate
from weaviate.classes.query import MetadataQuery
from weaviate.classes.config import Property, Configure, DataType, Integrations

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router: APIRouter = APIRouter()

@router.get('/problems-set/',response_model=List[ProblemResponseSchema])
def get_all_problems(db: Session = Depends(get_db)):
    return fetch_all_problems(db)

def fetch_all_problems(db: Session):
    return db.query(Problem).all()


@router.get('/problems', response_model=List[ProblemResponseSchema])
def get_search_query(
    value: str = Query(..., description="Search query string"),
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

    # ✅ Convert Weaviate results to your schema
    problems:List[ProblemResponseSchema] = []
    for obj in results.objects:
        props = obj.properties
        problem = ProblemResponseSchema(
            id=0,  # Replace if ID is stored
            slug="",  # Replace if available
            title=str(props.get("title", "")),
            description=str(props.get("description", "")),
            difficulty=str(props.get("difficulty", "")),
            tags=str(props.get("tags", "")),
            constraints=str(props.get("constraints", "")),
            hints=[],
            sample_testcases=[],
            dicussions=[],
            submissions=[],
            user_statuses=[]
        )
        problems.append(problem)

    return problems