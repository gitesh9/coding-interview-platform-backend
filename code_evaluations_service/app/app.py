from fastapi import FastAPI, Header
from .db.session import Base, engine, SessionLocal
from .db.models import Submission
from .api.sample_tests import run_sample_code
from .judge.judge import run_code, validate_sample
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from .get_service_client import get_problem
import json
import os
import jwt

app = FastAPI()
Base.metadata.create_all(bind=engine)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def _get_user_id_from_header(authorization: str) -> Optional[str]:
    """Extract user_id from Bearer token. Returns None if missing/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


class CodeSubmission(BaseModel):
    code: str
    language: str


class TestCaseResult(BaseModel):
    id: int
    input: str
    expectedOutput: str
    actualOutput: str
    passed: bool


class SubmissionResult(BaseModel):
    status: str
    runtime: Optional[str] = None
    memory: Optional[str] = None
    testCasesPassed: Optional[int] = None
    totalTestCases: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    testCaseResults: Optional[List[TestCaseResult]] = None


def _build_submission_result(raw_results: List[Dict[str, Any]], error: str = "", runtime: str = "") -> dict:
    """Convert internal judge results to frontend SubmissionResult format."""
    if error:
        return {
            "status": "Runtime Error" if "runtime" in error.lower() or "error" in error.lower() else "Compilation Error",
            "error": error,
            "runtime": runtime or None,
        }

    if not raw_results:
        return {"status": "Runtime Error", "error": "No results returned"}

    test_case_results = []
    passed_count = 0
    for i, r in enumerate(raw_results):
        is_passed = r.get("status") == "Accepted"
        if is_passed:
            passed_count += 1
        test_case_results.append({
            "id": i + 1,
            "input": str(r.get("Testcases", "")),
            "expectedOutput": str(r.get("expected", "")),
            "actualOutput": str(r.get("output", "")),
            "passed": is_passed,
        })

    total = len(test_case_results)
    all_passed = passed_count == total

    return {
        "status": "Accepted" if all_passed else "Wrong Answer",
        "runtime": runtime or None,
        "testCasesPassed": passed_count,
        "totalTestCases": total,
        "testCaseResults": test_case_results,
    }


def _extract_template_for_language(parsed_templates: dict, language: str) -> dict:
    if not isinstance(parsed_templates, dict):
        return {}
    lang_lower = (language or "").lower().strip()
    alias_map = {
        "py": ["python3", "python"],
        "python": ["python3", "python"],
        "python3": ["python3", "python"],
        "js": ["javascript", "js"],
        "javascript": ["javascript", "js"],
        "c++": ["cpp", "c++"],
        "cpp": ["cpp", "c++"],
        "golang": ["go", "golang"],
    }
    candidates = [language, lang_lower] + alias_map.get(lang_lower, [])
    for c in candidates:
        if c in parsed_templates and isinstance(parsed_templates[c], dict):
            return parsed_templates[c]
    # Fallback to python3 / python or first available dict template
    return parsed_templates.get("python3") or parsed_templates.get("python") or {}


@app.post("/{problemId}/evaluate")
async def eval_code(
    problemId: str,
    submission: CodeSubmission,
    authorization: str = Header(default=""),
):
    problem = get_problem(problemId, submission.language)
    if not problem:
        return {"status": "Runtime Error", "error": f"Problem '{problemId}' not found"}

    try:
        parsed = json.loads(problem.execution_template) if isinstance(problem.execution_template, str) else (problem.execution_template or {})
    except Exception:
        parsed = {}

    lang_template = _extract_template_for_language(parsed, submission.language)
    input_parser = lang_template.get('input_parser', '')
    function_call = lang_template.get('function_call', '')

    # For full evaluation we need hidden test cases — for now use sample testcases
    # via the same mechanism as /sample
    output, error, runtime, results = run_code(
        user_code=submission.code,
        input_data="",
        input_parsing=input_parser,
        function_call=function_call,
        language=submission.language,
    )

    if error:
        result = _build_submission_result([], error=error, runtime=runtime)
    else:
        try:
            parsed_results = json.loads(results) if results else []
        except Exception:
            parsed_results = []
        result = _build_submission_result(parsed_results, runtime=runtime)

    # Persist submission
    user_id = _get_user_id_from_header(authorization)
    if user_id:
        db = SessionLocal()
        try:
            p_id = 0
            if hasattr(problem, 'problem_id') and str(problem.problem_id).isdigit():
                p_id = int(problem.problem_id)
            elif str(problemId).isdigit():
                p_id = int(problemId)

            db_submission = Submission(
                problem_id=p_id,
                user_id=user_id,
                code=submission.code,
                language=submission.language,
                status=result["status"],
                runtime=result.get("runtime"),
                test_cases_passed=result.get("testCasesPassed"),
                total_test_cases=result.get("totalTestCases"),
            )
            db.add(db_submission)
            db.commit()
        except Exception as e:
            print(f"Error persisting submission: {e}")
            db.rollback()
        finally:
            db.close()

    return result


@app.post("/{problemId}/sample")
def eval_code_sample(problemId: str, submission: CodeSubmission):
    problem = get_problem(problemId, submission.language)
    if not problem:
        return {"status": "Runtime Error", "error": f"Problem '{problemId}' not found"}

    try:
        parsed = json.loads(problem.execution_template) if isinstance(problem.execution_template, str) else (problem.execution_template or {})
    except Exception:
        parsed = {}

    test_lang_template = parsed.get('python3', parsed.get('python', {}))
    client_lang_template = _extract_template_for_language(parsed, submission.language)
    if not client_lang_template:
        client_lang_template = test_lang_template

    # Fetch sample test input from the problem's input_schema / sample_testcases
    sample_input = ""  # run_sample_code will use problem.input_schema

    output, error, runtime, results = run_sample_code(
        submission.code,
        submission.language,
        sample_input,
        problem.input_schema,
        problem.official_solution,
        client_lang_template,
    )
    official_output, official_error, _, official_results = run_sample_code(
        problem.official_solution,
        'python',
        sample_input,
        problem.input_schema,
        problem.official_solution,
        test_lang_template,
    )

    if error:
        return _build_submission_result([], error=error, runtime=runtime)

    validation = validate_sample(official_results, results, sample_input, problem.input_schema)

    return _build_submission_result(validation, runtime=runtime)