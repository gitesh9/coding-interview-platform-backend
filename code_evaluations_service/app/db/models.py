from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, func
from .session import Base
import enum


class SupportedLanguages(enum.Enum):
    Python = "python"
    Java = "java"
    CPP = "cpp"
    C = "c"
    Rust = "rust"
    Go = "go"
    JavaScript = "javascript"


class SubmissionStatus(enum.Enum):
    Accepted = "Accepted"
    WrongAnswer = "Wrong Answer"
    RuntimeError = "Runtime Error"
    TimeLimitExceeded = "Time Limit Exceeded"
    CompilationError = "Compilation Error"


class HiddenTestcases(Base):
    __tablename__ = "testcases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, nullable=False, index=True)
    input_key = Column(Text)
    output_key = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    code = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    status = Column(String, nullable=False)
    runtime = Column(String, nullable=True)
    test_cases_passed = Column(Integer, nullable=True)
    total_test_cases = Column(Integer, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())