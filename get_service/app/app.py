from fastapi import FastAPI
import openai
from .routes import all_routes
from .db.session import Base, engine, SessionLocal
from .db.models.models import Problem
from .routes.problem.similar_problems import vector_store
app = FastAPI()
openai.api_key = "your-openai-api-key"
for sub_routes in all_routes:
    for route in sub_routes:
        app.include_router(route)
        
Base.metadata.create_all(bind=engine)

@app.on_event("startup") # type: ignore
def startup_event():
    db = SessionLocal()
    problems = db.query(Problem).all()

    for problem in problems:
        text = f"{problem.title} {problem.description} Tags: {problem.tags or ''}"
        vector_store.add(problem.id, text) # type: ignore
    
    vector_store.save()
    print("Vector index initialized with problems.")