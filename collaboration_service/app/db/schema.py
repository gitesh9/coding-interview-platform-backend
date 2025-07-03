from sqlalchemy import Column, Integer, Text, Boolean
from .session import Base

class Testcase(Base):
    __tablename__ = "testcases"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, nullable=False, primary_key=True)
    input_data = Column(Text)
    expected_output = Column(Text)
    is_sample = Column(Boolean, default=False)