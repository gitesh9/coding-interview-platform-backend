from fastapi import APIRouter
from fastapi.responses import JSONResponse

router: APIRouter = APIRouter()

@router.get('/user/{id}')
def user_details(id:int):
    return JSONResponse(content={"user":"abc","user_id":id},status_code=200)