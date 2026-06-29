from fastapi import FastAPI
from .router import router

app = FastAPI(
    title="To-Do API with Azure Service Bus",
    description="CRUD To-Do API that publishes creation events to an Azure "
                "Service Bus queue (producer-consumer async pattern).",
    version="2.0.0",
)

app.include_router(router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "docs": "/docs"}
