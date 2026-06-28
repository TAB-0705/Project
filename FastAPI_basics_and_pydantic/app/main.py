from fastapi import FastAPI
from .router import router

app = FastAPI(
    title="To-Do API",
    description="A simple CRUD To-Do API built with FastAPI and Pydantic.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "docs": "/docs"}
