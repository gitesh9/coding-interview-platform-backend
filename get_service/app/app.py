from fastapi import FastAPI
from .routes import all_routes
from .db.session import Base, engine

app = FastAPI()

for sub_routes in all_routes:
    for route in sub_routes:
        app.include_router(route)
        

Base.metadata.create_all(bind=engine)
