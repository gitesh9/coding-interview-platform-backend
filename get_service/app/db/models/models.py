from sqlalchemy import Column, Integer, String, Text, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ...db.session import Base
import enum
from datetime import datetime


class DifficultyEnum(enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
class SubmissionState(enum.Enum):
    successfull = "Accepted"
    failed = "Wrong"
    
class UserProblemStatusEnum(enum.Enum):
    solved = "solved"
    attempted = "attempted"
    not_attempted = "not_attempted"


class SampleTestcases(Base):
    __tablename__ = "sample_testcases"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    input_data = Column(Text)
    expected_output = Column(Text)
    is_sample = Column(Boolean, default=True)
    explanation = Column(Text, nullable=True)

    problem = relationship("Problem", back_populates="sample_testcases")

class Hint(Base):
    __tablename__ = "hints"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    text = Column(Text)

    problem = relationship("Problem", back_populates="hints")

class Discussion(Base):
    __tablename__ = "discussions"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    user_id = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    problem = relationship("Problem", back_populates="discussions")
    
class UserProblemStatus(Base):
    __tablename__ = "user_problem_status"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"),index=True)
    status = Column(Enum(UserProblemStatusEnum, name="problem_status"), nullable=False)

    # Optionally add timestamps or counters
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    problem = relationship("Problem", back_populates="user_statuses")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"),index=True)
    user_id = Column(Integer, nullable=False, index=True)
    code = Column(Text)
    language = Column(String)
    status = Column(Enum(SubmissionState),nullable=False)
    submitted_at = Column(DateTime, default=datetime.now)

    problem = relationship("Problem", back_populates="submissions")

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(Text, index=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(DifficultyEnum), nullable=False, index=True)
    tags = Column(Text, nullable=True, index=True)
    constraints = Column(Text, nullable=True)

    hints = relationship("Hint", back_populates="problem", cascade="all, delete-orphan")
    sample_testcases = relationship("SampleTestcases", back_populates="problem", cascade="all, delete-orphan")
    discussions = relationship("Discussion", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")
    user_statuses = relationship("UserProblemStatus", back_populates="problem", cascade="all, delete-orphan")
    