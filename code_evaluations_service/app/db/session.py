from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

print("eval Service: ",  os.getenv("CODE_EVAL_SERVICE_URL"))
DATABASE_URL: str = os.getenv("CODE_EVAL_SERVICE_URL","")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
