import uuid
import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db.session import Base, engine, SessionLocal
from .db.models import InterviewSession, SessionStatus, User, Problem
from .auth import get_current_user_id

app = FastAPI()
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Request / response schemas ──────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    problemIds: List[int]
    timeLimit: int = 45


class JoinSessionRequest(BaseModel):
    joinCode: str


class InterviewSessionResponse(BaseModel):
    id: str
    interviewerId: str
    candidateId: Optional[str] = None
    candidateName: Optional[str] = None
    problemIds: List[int]
    problemTitles: Optional[List[str]] = None
    timeLimit: int
    status: str
    joinCode: str
    createdAt: datetime
    scheduledAt: Optional[datetime] = None

    class Config:
        orm_mode = True


def _to_response(session: InterviewSession) -> dict:
    return {
        "id": session.id,
        "interviewerId": session.interviewer_id,
        "candidateId": session.candidate_id,
        "candidateName": session.candidate_name,
        "problemIds": session.problem_ids or [],
        "problemTitles": session.problem_titles or [],
        "timeLimit": session.time_limit,
        "status": session.status.value if hasattr(session.status, "value") else session.status,
        "joinCode": session.join_code,
        "createdAt": session.created_at.isoformat() if session.created_at else None,
        "scheduledAt": session.scheduled_at.isoformat() if session.scheduled_at else None,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/sessions")
def list_sessions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return all sessions where the user is the interviewer."""
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.interviewer_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    return [_to_response(s) for s in sessions]


@app.post("/sessions")
def create_session(
    data: CreateSessionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    join_code = secrets.token_urlsafe(6).upper()[:8]

    # Resolve problem titles from IDs
    problem_titles = []
    if data.problemIds:
        problems = db.query(Problem).filter(Problem.id.in_(data.problemIds)).all()
        title_map = {p.id: p.title for p in problems}
        problem_titles = [title_map.get(pid, "") for pid in data.problemIds]

    session = InterviewSession(
        id=str(uuid.uuid4()),
        interviewer_id=user_id,
        problem_ids=data.problemIds,
        problem_titles=problem_titles,
        time_limit=data.timeLimit,
        status=SessionStatus.waiting,
        join_code=join_code,
        created_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_response(session)


@app.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_response(session)


@app.post("/sessions/join")
def join_session(
    data: JoinSessionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.join_code == data.joinCode)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Invalid join code")
    if session.status != SessionStatus.waiting:
        raise HTTPException(status_code=400, detail="Session is not available to join")

    session.candidate_id = user_id
    # Look up candidate name from users table
    user = db.query(User).filter(User.id == int(user_id)).first()
    session.candidate_name = user.name if user else None
    session.status = SessionStatus.active
    db.commit()
    db.refresh(session)
    return _to_response(session)


@app.patch("/sessions/{session_id}/end")
def end_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.interviewer_id != user_id:
        raise HTTPException(status_code=403, detail="Only the interviewer can end the session")

    session.status = SessionStatus.completed
    db.commit()
    db.refresh(session)
    return _to_response(session)
