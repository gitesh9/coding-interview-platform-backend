from sqlalchemy import Column, Integer, String, DateTime, Enum, ARRAY
from ..db.session import Base
from datetime import datetime
import enum


class SessionStatus(enum.Enum):
    waiting = "waiting"
    active = "active"
    completed = "completed"


class User(Base):
    """Read-only mirror of auth_service users table (same DB)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)


class Problem(Base):
    """Read-only mirror of get_service problems table (same DB)."""
    __tablename__ = "problems"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True)
    interviewer_id = Column(String, nullable=False, index=True)
    candidate_id = Column(String, nullable=True)
    candidate_name = Column(String, nullable=True)
    problem_ids = Column(ARRAY(Integer), nullable=False, default=[])
    problem_titles = Column(ARRAY(String), nullable=True, default=[])
    time_limit = Column(Integer, nullable=False, default=45)
    status = Column(Enum(SessionStatus, name="session_status"), nullable=False, default=SessionStatus.waiting)
    join_code = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)
