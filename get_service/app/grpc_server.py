# grpc_server.py

import grpc
from concurrent import futures
from .problem_pb2_grpc import ProblemServiceServicer, add_ProblemServiceServicer_to_server  # type: ignore
from . import problem_pb2
from .db.session import SessionLocal
from .db.models.models import Problem
import json


class ProblemService(ProblemServiceServicer):
    def GetProblemById(self, request, context):  # type: ignore
        db = SessionLocal()
        try:
            req_id = str(request.problem_id or "").strip()
            query = db.query(Problem)
            problem = None

            # 1. Try numeric ID if req_id is digits
            if req_id.isdigit():
                problem = query.filter(Problem.id == int(req_id)).first()

            # 2. Try slug (case-insensitive)
            if not problem and req_id:
                problem = query.filter(Problem.slug.ilike(req_id)).first()

            # 3. Try exact slug match
            if not problem and req_id:
                problem = query.filter(Problem.slug == req_id).first()

            # 4. Try title match as fallback
            if not problem and req_id:
                problem = query.filter(Problem.title.ilike(req_id)).first()

            if not problem:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Problem '{req_id}' not found")
                return problem_pb2.GetProblemResponse()

            # Normalize execution_template
            exec_tmpl = problem.execution_template
            if isinstance(exec_tmpl, str):
                try:
                    exec_tmpl = json.loads(exec_tmpl)
                except Exception:
                    exec_tmpl = {}
            elif not isinstance(exec_tmpl, dict):
                exec_tmpl = {}

            python_tmpl = exec_tmpl.get("python3") or exec_tmpl.get("python") or {}

            req_lang = str(request.language or "").lower().strip()
            lang_alias_map = {
                "py": "python3",
                "python": "python3",
                "python3": "python3",
                "js": "javascript",
                "javascript": "javascript",
                "c++": "cpp",
                "cpp": "cpp",
                "c": "c",
                "java": "java",
                "rust": "rust",
                "go": "go",
                "golang": "go",
            }
            canonical_lang = lang_alias_map.get(req_lang, req_lang)

            selected_tmpl = (
                exec_tmpl.get(canonical_lang)
                or exec_tmpl.get(req_lang)
                or exec_tmpl.get(request.language)
                or python_tmpl
            )

            template = {
                "python3": python_tmpl,
                "python": python_tmpl,
                canonical_lang: selected_tmpl,
                req_lang: selected_tmpl,
            }
            if isinstance(exec_tmpl, dict):
                for k, v in exec_tmpl.items():
                    if k not in template:
                        template[k] = v

            input_schema_str = "{}"
            if isinstance(problem.input_schema, (dict, list)):
                input_schema_str = json.dumps(problem.input_schema)
            elif isinstance(problem.input_schema, str):
                input_schema_str = problem.input_schema

            return problem_pb2.GetProblemResponse(
                problem_id=str(problem.id),
                title=str(problem.title or ""),
                input_schema=input_schema_str,
                official_solution=str(problem.official_solution or ""),
                constraints=str(problem.constraints or ""),
                execution_template=json.dumps(template),
            )
        except Exception as e:
            print(f"Error in GetProblemById: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return problem_pb2.GetProblemResponse()
        finally:
            db.close()


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ProblemServiceServicer_to_server(ProblemService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server running on port 50051...")
    server.start()
    server.wait_for_termination()
