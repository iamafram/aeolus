from fastapi import FastAPI
from api.routes.auth import router as auth_router

app = FastAPI(
    title="Marathon Coach API",
    description="AI-powered training coach for the NYC Marathon",
    version="0.1.0",
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}