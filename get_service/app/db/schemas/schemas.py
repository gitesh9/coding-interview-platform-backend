from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

from ..enums import DifficultyEnum, SubmissionState, UserProblemStatusEnum

# The API capitalises difficulty; the DB enum stores it lowercase.
ApiDifficulty = Literal["Easy", "Medium", "Hard"]


class HintSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str


class SampleTestcasesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    input_data: str
    expected_output: str
    explanation: Optional[str] = None


class DiscussionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    comment: str
    created_at: datetime


class UserProblemStatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    problem_id: int
    status: UserProblemStatusEnum
    last_updated: datetime


class SubmissionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    user_id: int
    code: str
    language: str
    status: SubmissionState
    submitted_at: datetime


class ProblemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    slug: str
    title: str
    description: str
    difficulty: DifficultyEnum
    tags: Optional[str] = None
    constraints: Optional[str] = None
    hints: List[HintSchema] = []
    sample_testcases: List[SampleTestcasesSchema] = []
    discussions: List[DiscussionSchema] = []
    submissions: List[SubmissionSchema] = []
    user_statuses: List[UserProblemStatusSchema] = []


class SimilarProblemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    slug: str
    title: str
    difficulty: DifficultyEnum


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
    """Matches frontend ProblemListItem, whose difficulty is a plain string."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    difficulty: str
    tags: Optional[str] = None
    constraints: Optional[str] = None
    description: str
    isSolved: Optional[bool] = None


class ProblemDetailSchema(BaseModel):
    """Matches frontend Problem interface."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    difficulty: ApiDifficulty
    description: str
    examples: List[ExampleSchema] = []
    constraints: List[str] = []
    starterCode: Dict[str, str] = {}
    testCases: List[TestCaseSchema] = []
    isSolved: Optional[bool] = None