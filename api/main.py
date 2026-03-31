from fastapi import FastAPI
from api.routes.auth import router as auth_router
from pipeline.models import init_db

app = FastAPI(
    title="Marathon Coach API",
    description="AI-powered training coach for the NYC Marathon",
    version="0.1.0",
)

app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}