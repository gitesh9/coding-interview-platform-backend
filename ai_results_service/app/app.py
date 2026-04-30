import openai
from fastapi import FastAPI
app = FastAPI()
openai.api_key = "your-openai-api-key"

@app.post("/{problemId}/generate")
def generate(problemId: str):
    pass

def generate_hint(problemId: str):
    pass

def generate_problem_description(problemId: str):
    pass

def generate_solution_suggestions(problemId: str):
    pass