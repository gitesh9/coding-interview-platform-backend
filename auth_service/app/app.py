from fastapi import FastAPI, HTTPException, Depends
from .db.session import Base, engine
from .db.schema import User
from .db.db_requests import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from auth_utils import create_access_token, verify_password
from typing import Dict, Any
app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

@app.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": credentials.username})
    return LoginResponse(access_token=access_token, token_type="bearer")


class RegisterRequest(BaseModel):
    username: str
    user_email: str
    password: str

@app.post("/register")
def register(user: RegisterRequest,db: Session = Depends(get_db))-> Dict[str,Any]:
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.user_email == user.user_email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_user = User(username=user.username, user_email=user.user_email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "id": new_user.id}

Base.metadata.create_all(bind=engine)