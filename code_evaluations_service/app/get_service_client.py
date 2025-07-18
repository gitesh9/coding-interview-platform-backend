from typing import Dict, Union

def get_input_schema(problem_id:str)->Dict[str,str]:
    input_schema = {"":""}
    return input_schema

import grpc
from pydantic import BaseModel

from . import problem_pb2
from . import problem_pb2_grpc


class Problem(BaseModel):
    problem_id: int
    title: str
    input_schema: str
    official_solution: str
    constraints: str
    execution_template: str


def get_problem(problem_id: str,lang:str) -> Union[Problem, None]:
    
    channel = grpc.insecure_channel("get_service:50051")
    stub = problem_pb2_grpc.ProblemServiceStub(channel)
    request = problem_pb2.GetProblemRequest(problem_id=problem_id,language=lang) # type: ignore
    try:
        response = stub.GetProblemById(request) # type: ignore
        print("Fetched Problem:")
        print(f"Title: {response.title}") # type: ignore
        print(f"Schema: {response.input_schema}") # type: ignore
        print(f"Solution: {response.official_solution}") # type: ignore
        print(f"Constraints: {response.constraints}") # type: ignore
        return response # type: ignore
    except grpc.RpcError as e:
        print(f"gRPC error: {e.code()} - {e.details()}")
        return None


    # return Problem(
    #     problem_id=response.problem_id,# type: ignore
    #     title=response.title,# type: ignore
    #     input_schema=response.input_schema,# type: ignore
    #     official_solution=response.official_solution,# type: ignore
    #     constraints=response.constraints# type: ignore
    # )

# if __name__ == "__main__":
#     problem: Problem = get_problem("121")
#     print(problem.model_dump_json(indent=2))
