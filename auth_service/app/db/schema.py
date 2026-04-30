from sqlalchemy import Column, Integer, String, Enum
from .session import Base
import enum


class RoleEnum(enum.Enum):
    interviewer = "interviewer"
    candidate = "candidate"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum, name="user_role"), nullable=False, default=RoleEnum.candidate)
