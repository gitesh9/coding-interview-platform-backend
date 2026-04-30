from fastapi import FastAPI, HTTPException, Depends
from .db.session import Base, engine
from .db.schema import User
from .db.db_requests import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .auth_utils import create_access_token, verify_password, hash_password
from typing import Dict, Any, Optional

app = FastAPI()


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatarUrl: Optional[str] = None

    class Config:
        orm_mode = True


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str


def _build_auth_response(user: User) -> Dict[str, Any]:
    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})
    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "avatarUrl": None,
        },
    }


@app.post("/login", response_model=AuthResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _build_auth_response(user)


@app.post("/register", response_model=AuthResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _build_auth_response(new_user)


Base.metadata.create_all(bind=engine)