from fastapi import FastAPI

from apps.api.routes.sessions import router as sessions_router

app = FastAPI(title="MealPilot API")
app.include_router(sessions_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
