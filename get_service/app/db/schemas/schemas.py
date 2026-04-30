from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import enum

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
    
class HintSchema(BaseModel):
    text: str
    
    class Config:
        orm_mode = True


class SampleTestcasesSchema(BaseModel):
    input_data :str
    expected_output: str
    explanation: str
    
    class Config:
        orm_mode = True 

class DiscussionSchema(BaseModel):
    user_id: int
    comment: str
    created_at: datetime

    class Config:
        orm_mode = True 
    
class UserProblemStatusSchema(BaseModel):
    problem_id: int
    status: str
    last_updated: datetime

    class Config:
        orm_mode = True
        use_enum_values = True

class SubmissionSchema(BaseModel):
    user_id: int
    code: str
    language: str
    status: str
    submitted_at:datetime

    class Config:
        orm_mode = True 
        use_enum_values = True
    
class ProblemResponseSchema(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    difficulty: str
    tags: Optional[str]
    constraints: Optional[str]
    hints: List[HintSchema] = []
    sample_testcases: List[SampleTestcasesSchema] =[]
    dicussions: List[DiscussionSchema] = []
    submissions: List[SubmissionSchema]=[]
    user_statuses: List[UserProblemStatusSchema]=[]
    
    class Config:
        orm_mode = True
        use_enum_values = True

class SimilarProblemResponseSchema(BaseModel):
    id: int
    slug: str
    title: str
    difficulty: str
    class Config:
        orm_mode = True


# ─── Frontend-compatible schemas ─────────────────────────────────────────────

class ExampleSchema(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None

class TestCaseSchema(BaseModel):
    id: int
    input: str
    expectedOutput: str

class ProblemListItemSchema(BaseModel):
    """Matches frontend ProblemListItem interface."""
    id: int
    slug: str
    title: str
    difficulty: str
    tags: Optional[str] = None
    constraints: Optional[str] = None
    description: str
    isSolved: Optional[bool] = None

    class Config:
        orm_mode = True
        use_enum_values = True

class ProblemDetailSchema(BaseModel):
    """Matches frontend Problem interface."""
    id: int
    title: str
    difficulty: str
    description: str
    examples: List[ExampleSchema] = []
    constraints: List[str] = []
    starterCode: Dict[str, str] = {}
    testCases: List[TestCaseSchema] = []
    isSolved: Optional[bool] = None

    class Config:
        orm_mode = True
        use_enum_values = True