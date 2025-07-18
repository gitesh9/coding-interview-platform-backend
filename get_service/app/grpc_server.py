# grpc_server.py

import grpc
from concurrent import futures
from .problem_pb2_grpc import ProblemServiceServicer, add_ProblemServiceServicer_to_server  # type: ignore
from . import problem_pb2
from .db.session import SessionLocal
import json


class ProblemService(ProblemServiceServicer):
    def GetProblemById(self, request, context):# type: ignore # Add full types if you like
        from .app import Problem
        db = SessionLocal()
        try:
            problem: Problem = db.query(Problem).filter(Problem.id == request.problem_id).first() # type: ignore
            if not problem:
                context.set_code(grpc.StatusCode.NOT_FOUND) # type: ignore
                context.set_details("Problem not found") # type: ignore
                return problem_pb2.GetProblemResponse() # type: ignore
            
            if request.language in ['python3','python']: # type: ignore
                template = {"python3":problem.execution_template["python3"]}
            else:
                template = {request.language:problem.execution_template[request.language],"python3":problem.execution_template["python3"]} # type: ignore
            
            return problem_pb2.GetProblemResponse( # type: ignore
                problem_id=str(problem.id),
                title=str(problem.title or ""),
                input_schema=json.dumps(problem.input_schema or {}),
                official_solution=str(problem.official_solution or ""),
                constraints=str(problem.constraints or ""),
                execution_template = json.dumps(template) # type: ignore
            )
        finally:
            db.close()


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ProblemServiceServicer_to_server(ProblemService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server running on port 50051...")
    server.start()
    server.wait_for_termination()
