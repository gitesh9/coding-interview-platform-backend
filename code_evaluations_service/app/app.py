from fastapi import FastAPI
from .db.session import Base, engine
from .api.sample_tests import run_sample_code
from .judge.judge import run_code, validate_sample
from pydantic import BaseModel
from typing import Dict
from .get_service_client import get_problem
import json

app = FastAPI()
Base.metadata.create_all(bind=engine)

class SampleTest(BaseModel):
    code: str
    input: str
    language: str
class CodeSubmission(BaseModel):
    code: str
    input: str
    input_parsing: str
    function_call: str
    language: str

@app.post("/{problemId}/evaluate")
async def eval_code(problemId: str,submission: CodeSubmission)->Dict[str,str]:
    output, error, runtime, results = run_code( # type: ignore
        user_code=submission.code,
        input_data=submission.input,
        input_parsing=submission.input_parsing,
        function_call=submission.function_call,
        language=submission.language
    )
    return {"output": output, "error": error, "runtime":runtime}

@app.post("/{problemId}/sample")
def eval_code_sample(problemId:str, sample_test: SampleTest):
    problem = get_problem(problemId,sample_test.language)
    parsed = json.loads(problem.execution_template) # type: ignore
    test_lang_template = parsed['python3']
    client_lang_template = parsed[sample_test.language]
    if problem:
        output, error, runtime, results = run_sample_code(sample_test.code,sample_test.language,sample_test.input, problem.input_schema, problem.official_solution, client_lang_template) # type: ignore
        official_output, official_error, runtime, official_results = run_sample_code(problem.official_solution,'python',sample_test.input, problem.input_schema, problem.official_solution, test_lang_template) # type: ignore
        print(official_error,error,official_results)
        if error:
            return error
        validation = validate_sample(official_results,results,sample_test.input,problem.input_schema)
        return validation