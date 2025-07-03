from sqlalchemy import Table, Column, Integer, String, Text, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ...db.session import Base
import enum
from datetime import datetime


class DifficultyEnum(enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
class SubmissionState(enum.Enum):
    successfull = "successfull"
    failed = "failed"
    
user_solved_problems = Table(
    "user_solved_problems",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("problem_id", Integer, ForeignKey("problems.id"), primary_key=True)
)

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(DifficultyEnum), nullable=False)

    hints = relationship("Hint", back_populates="problem", cascade="all, delete-orphan")
    testcases = relationship("Testcase", back_populates="problem", cascade="all, delete-orphan")
    discussions = relationship("Discussion", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")
    solvers = relationship(
        "User",
        secondary=user_solved_problems,
        back_populates="solved_problems"
    )

class Hint(Base):
    __tablename__ = "hints"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    text = Column(Text)

    problem = relationship("Problem", back_populates="hints")

class Testcase(Base):
    __tablename__ = "testcases"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    input_data = Column(Text)
    expected_output = Column(Text)
    is_sample = Column(Boolean, default=False)

    problem = relationship("Problem", back_populates="testcases")

class Discussion(Base):
    __tablename__ = "discussions"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    user_id = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    problem = relationship("Problem", back_populates="discussions")
    user = relationship("User")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    user_id = Column(Integer, nullable=False)
    code = Column(Text)
    language = Column(String)
    status = Column(Enum(SubmissionState),nullable=False)
    submitted_at = Column(DateTime, default=datetime.now)

    problem = relationship("Problem", back_populates="submissions")
    user = relationship("User")
