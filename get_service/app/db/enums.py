"""Domain enums shared by the ORM models and the Pydantic schemas."""

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
