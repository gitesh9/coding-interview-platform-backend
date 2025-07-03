from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import Depends
from sqlalchemy.orm import Session
from ...db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router: APIRouter = APIRouter()
@router.get('/problems/{problemId}')
def get_problem_details(problemId:int,db: Session = Depends(get_db)):
    print(problemId)
    return JSONResponse(content={"status":"successful"},status_code=200)