import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
from app.core.database import engine
from app import models  # noqa: F401 -- ensures all models are registered on Base.metadata
from app.api.v1.router import api_router

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

# CORS: tighten allow_origins to the real frontend URL(s) in production.
allowed_origins = [origin.strip() for origin in settings.FRONTEND_URLS.split(",") if origin.strip()]
if settings.ENV == "development" and not allowed_origins:
    allowed_origins = ["http://127.0.0.1:5173", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}
