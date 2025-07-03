from db.session import SessionLocal  # adjust the import to match your project structure
from sqlalchemy.orm import Session
from collections.abc import Generator  # for type hints in yield-based deps
from sqlalchemy.orm import Session

def get_db()-> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()