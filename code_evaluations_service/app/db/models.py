from sqlalchemy import Column, Integer, Text, DateTime, func
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
class HiddenTestcases(Base):
    __tablename__ = "testcases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, nullable=False, primary_key=True, index=True)
    input_key = Column(Text)
    output_key = Column(Text)
    created_at = Column(DateTime(timezone=True),server_default=func.now())