from sqlalchemy import Column, Integer, String
from .session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    user_email = Column(String, unique=True, nullable=False)