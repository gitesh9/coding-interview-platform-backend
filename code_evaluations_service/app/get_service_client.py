import json
import os
from typing import Dict, Union, Optional
import grpc
from pydantic import BaseModel

from . import problem_pb2
from . import problem_pb2_grpc


def get_input_schema(problem_id: str) -> Dict[str, str]:
    return {"": ""}


class Problem(BaseModel):
    problem_id: str
    title: str
    input_schema: str
    official_solution: str
    constraints: str
    execution_template: str


GET_SERVICE_GRPC_HOST = os.getenv("GET_SERVICE_GRPC_HOST", "get_service:50051")


def _get_problem_from_db_fallback(problem_id: str, lang: str) -> Optional[Problem]:
    """Fallback directly to the database if gRPC is unavailable or fails."""
    try:
        from sqlalchemy import text
        from .db.session import SessionLocal

        db = SessionLocal()
        try:
            req_id = str(problem_id or "").strip()
            row = None
            if req_id.isdigit():
                row = db.execute(
                    text("SELECT id, title, input_schema, official_solution, constraints, execution_template FROM problems WHERE id = :pid LIMIT 1"),
                    {"pid": int(req_id)}
                ).first()

            if not row and req_id:
                row = db.execute(
                    text("SELECT id, title, input_schema, official_solution, constraints, execution_template FROM problems WHERE LOWER(slug) = LOWER(:slug) LIMIT 1"),
                    {"slug": req_id}
                ).first()

            if not row and req_id:
                row = db.execute(
                    text("SELECT id, title, input_schema, official_solution, constraints, execution_template FROM problems WHERE LOWER(title) = LOWER(:title) LIMIT 1"),
                    {"title": req_id}
                ).first()

            if row:
                exec_tmpl = row[5]
                if isinstance(exec_tmpl, str):
                    try:
                        parsed_tmpl = json.loads(exec_tmpl)
                    except Exception:
                        parsed_tmpl = {}
                elif isinstance(exec_tmpl, dict):
                    parsed_tmpl = exec_tmpl
                else:
                    parsed_tmpl = {}

                input_schema = row[2]
                if isinstance(input_schema, (dict, list)):
                    input_schema_str = json.dumps(input_schema)
                elif isinstance(input_schema, str):
                    input_schema_str = input_schema
                else:
                    input_schema_str = "{}"

                try:
                    tc_rows = db.execute(
                        text("SELECT id, input_data, expected_output, explanation FROM sample_testcases WHERE problem_id = :pid ORDER BY id"),
                        {"pid": row[0]}
                    ).fetchall()
                    parsed_tmpl["sample_testcases"] = [
                        {
                            "id": r[0],
                            "input": str(r[1] or ""),
                            "expectedOutput": str(r[2] or ""),
                            "explanation": str(r[3] or ""),
                        }
                        for r in tc_rows
                    ]
                except Exception as tc_err:
                    print(f"Could not load sample testcases for problem {row[0]}: {tc_err}")

                return Problem(
                    problem_id=str(row[0]),
                    title=str(row[1] or ""),
                    input_schema=input_schema_str,
                    official_solution=str(row[3] or ""),
                    constraints=str(row[4] or ""),
                    execution_template=json.dumps(parsed_tmpl),
                )
        finally:
            db.close()
    except Exception as e:
        print(f"DB fallback query error for problem {problem_id}: {e}")
    return None


def get_problem(problem_id: str, lang: str) -> Union[Problem, problem_pb2.GetProblemResponse, None]:
    channel = grpc.insecure_channel(GET_SERVICE_GRPC_HOST)
    stub = problem_pb2_grpc.ProblemServiceStub(channel)
    request = problem_pb2.GetProblemRequest(problem_id=str(problem_id), language=lang)
    try:
        response = stub.GetProblemById(request, timeout=5.0)
        if response and response.problem_id:
            print(f"Fetched Problem via gRPC: {response.title} (ID: {response.problem_id})")
            return response
        else:
            print(f"gRPC returned empty response for problem {problem_id}")
    except grpc.RpcError as e:
        print(f"gRPC error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"Error calling gRPC get_problem: {e}")

    # Fallback to database query if gRPC is unavailable or problem wasn't resolved over gRPC
    print(f"Attempting database fallback for problem '{problem_id}'...")
    db_problem = _get_problem_from_db_fallback(problem_id, lang)
    if db_problem:
        print(f"Fetched Problem via DB fallback: {db_problem.title} (ID: {db_problem.problem_id})")
        return db_problem

    return None
