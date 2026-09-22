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


def _normalize_output(val: Any) -> str:
    if val is None:
        return ""
    val_str = str(val).strip()
    try:
        parsed = json.loads(val_str)
        return json.dumps(parsed, sort_keys=True)
    except Exception:
        lines = [l.strip() for l in val_str.splitlines() if l.strip()]
        return "\n".join(lines)


def _compare_outputs(actual: str, expected: str) -> bool:
    if actual == expected:
        return True
    if not actual and not expected:
        return True
    norm_actual = _normalize_output(actual)
    norm_expected = _normalize_output(expected)
    if norm_actual == norm_expected:
        return True
    if norm_actual.lower() == norm_expected.lower():
        return True
    return False


def _fetch_sample_testcases(problem, parsed_tmpl: dict, problem_id_str: str) -> List[Dict[str, Any]]:
    # 1. Check embedded in parsed execution_template
    if isinstance(parsed_tmpl, dict) and "sample_testcases" in parsed_tmpl:
        tcs = parsed_tmpl.get("sample_testcases")
        if isinstance(tcs, list) and len(tcs) > 0:
            return tcs

    # 2. Query direct from DB sample_testcases table
    pid = None
    if hasattr(problem, 'problem_id') and str(problem.problem_id).isdigit():
        pid = int(problem.problem_id)
    elif str(problem_id_str).isdigit():
        pid = int(problem_id_str)

    if pid is not None:
        try:
            from sqlalchemy import text
            db = SessionLocal()
            try:
                rows = db.execute(
                    text("SELECT id, input_data, expected_output, explanation FROM sample_testcases WHERE problem_id = :pid ORDER BY id"),
                    {"pid": pid}
                ).fetchall()
                if rows:
                    return [
                        {
                            "id": r[0],
                            "input": str(r[1] or ""),
                            "expectedOutput": str(r[2] or ""),
                            "explanation": str(r[3] or ""),
                        }
                        for r in rows
                    ]
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching sample_testcases from DB: {e}")

    return []


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
    try:
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

        sample_testcases = _fetch_sample_testcases(problem, parsed, problemId)
        if not sample_testcases:
            sample_testcases = [{"id": 1, "input": "", "expectedOutput": ""}]

        test_case_results = []
        passed_count = 0
        overall_error = ""
        last_runtime = "0"

        for i, tc in enumerate(sample_testcases):
            tc_input = str(tc.get("input") or "")
            tc_expected = str(tc.get("expectedOutput") or "")
            tc_id = tc.get("id") or (i + 1)

            output, error, runtime, _ = run_code(
                user_code=submission.code,
                input_data=tc_input,
                input_parsing=input_parser,
                function_call=function_call,
                language=submission.language,
            )

            if runtime and runtime != "-1":
                last_runtime = runtime

            if error:
                overall_error = error
                test_case_results.append({
                    "id": tc_id,
                    "input": tc_input,
                    "expectedOutput": tc_expected,
                    "actualOutput": "",
                    "passed": False,
                })
            else:
                passed = _compare_outputs(output, tc_expected)
                if passed:
                    passed_count += 1
                test_case_results.append({
                    "id": tc_id,
                    "input": tc_input,
                    "expectedOutput": tc_expected,
                    "actualOutput": output,
                    "passed": passed,
                })

        total = len(test_case_results)
        if overall_error and passed_count == 0:
            status = "Runtime Error" if ("runtime" in overall_error.lower() or "error" in overall_error.lower() or "traceback" in overall_error.lower()) else "Compilation Error"
            result = {
                "status": status,
                "error": overall_error,
                "runtime": last_runtime,
                "testCasesPassed": 0,
                "totalTestCases": total,
                "testCaseResults": test_case_results,
            }
        else:
            result = {
                "status": "Accepted" if passed_count == total else "Wrong Answer",
                "runtime": last_runtime,
                "error": overall_error or None,
                "testCasesPassed": passed_count,
                "totalTestCases": total,
                "testCaseResults": test_case_results,
            }

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

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "Runtime Error",
            "error": f"Evaluation error: {str(e)}",
            "testCasesPassed": 0,
            "totalTestCases": 0,
            "testCaseResults": [],
        }


@app.post("/{problemId}/sample")
def eval_code_sample(problemId: str, submission: CodeSubmission):
    try:
        problem = get_problem(problemId, submission.language)
        if not problem:
            return {
                "status": "Runtime Error",
                "error": f"Problem '{problemId}' not found",
                "testCasesPassed": 0,
                "totalTestCases": 0,
                "testCaseResults": [],
            }

        try:
            parsed = json.loads(problem.execution_template) if isinstance(problem.execution_template, str) else (problem.execution_template or {})
        except Exception:
            parsed = {}

        client_lang_template = _extract_template_for_language(parsed, submission.language)
        input_parser = client_lang_template.get('input_parser', '')
        function_call = client_lang_template.get('function_call', '')

        # Fetch sample test cases
        sample_testcases = _fetch_sample_testcases(problem, parsed, problemId)
        if not sample_testcases:
            sample_testcases = [{"id": 1, "input": "", "expectedOutput": ""}]

        test_case_results = []
        passed_count = 0
        overall_error = ""
        last_runtime = "0"

        for i, tc in enumerate(sample_testcases):
            tc_input = str(tc.get("input") or "")
            tc_expected = str(tc.get("expectedOutput") or "")
            tc_id = tc.get("id") or (i + 1)

            output, error, runtime, _ = run_code(
                user_code=submission.code,
                input_data=tc_input,
                input_parsing=input_parser,
                function_call=function_call,
                language=submission.language,
            )

            if runtime and runtime != "-1":
                last_runtime = runtime

            if error:
                overall_error = error
                test_case_results.append({
                    "id": tc_id,
                    "input": tc_input,
                    "expectedOutput": tc_expected,
                    "actualOutput": "",
                    "passed": False,
                })
            else:
                passed = _compare_outputs(output, tc_expected)
                if passed:
                    passed_count += 1
                test_case_results.append({
                    "id": tc_id,
                    "input": tc_input,
                    "expectedOutput": tc_expected,
                    "actualOutput": output,
                    "passed": passed,
                })

        total = len(test_case_results)
        if overall_error and passed_count == 0:
            status = "Runtime Error" if ("runtime" in overall_error.lower() or "error" in overall_error.lower() or "traceback" in overall_error.lower()) else "Compilation Error"
            return {
                "status": status,
                "error": overall_error,
                "runtime": last_runtime,
                "testCasesPassed": 0,
                "totalTestCases": total,
                "testCaseResults": test_case_results,
            }

        status = "Accepted" if passed_count == total else "Wrong Answer"
        return {
            "status": status,
            "runtime": last_runtime,
            "error": overall_error or None,
            "testCasesPassed": passed_count,
            "totalTestCases": total,
            "testCaseResults": test_case_results,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "Runtime Error",
            "error": f"Evaluation error: {str(e)}",
            "testCasesPassed": 0,
            "totalTestCases": 0,
            "testCaseResults": [],
        }