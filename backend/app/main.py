from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Mausam backend is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get(
    "/metrics",
    include_in_schema=False,
)
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )