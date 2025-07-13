from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import Depends
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db.models.models import Problem
from ...db.schemas.schemas import ProblemResponseSchema,SimilarProblemResponseSchema
from sqlalchemy.orm import Session
from typing import Dict, List, Union
from .similar_problems import vector_store

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router: APIRouter = APIRouter()

@router.get('/problems/{value}',response_model=Dict[str, Union[ProblemResponseSchema, List[SimilarProblemResponseSchema]]])
def get_problem_details(value:str,db: Session = Depends(get_db)) -> Union[JSONResponse, Dict[str, Union[ProblemResponseSchema, List[SimilarProblemResponseSchema]]]]:
    # problem_data = get_problem_data(value)
    query = db.query(Problem)
    if value.isdigit():
        problem_data: ProblemResponseSchema = query.filter(Problem.id == value).first()
    else:
        problem_data: ProblemResponseSchema = query.filter(Problem.slug.ilike(value)).first()
    if not problem_data:
        return JSONResponse(
            status_code=404,
            content={"error": 404, "message": "Problem not found"}
        )
        
    filtered_similar_problems = find_similar_problems(problem_data, db)
    
    print("HELLOOOO: ",filtered_similar_problems)
    return {"problem_detail": problem_data, "similar_problems": filtered_similar_problems}

def find_similar_problems(problem:Problem, db:Session)->List[Problem]:
    text = f"{problem.title} {problem.description} Tags: {problem.tags or ''}"
    similar_ids = vector_store.search(text,problem.id) # type: ignore
    similar_problems = db.query(Problem).filter(Problem.id.in_(similar_ids)).all()

    return similar_problems