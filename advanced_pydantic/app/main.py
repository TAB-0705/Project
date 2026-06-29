from fastapi import FastAPI
from .router import router

app = FastAPI(
    title="Member Registration API",
    description="FastAPI app using advanced Pydantic validators for strict "
                "business logic (regex IDs, age verification, password rules).",
    version="1.0.0",
)

app.include_router(router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "docs": "/docs"}
