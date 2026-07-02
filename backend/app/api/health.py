from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    project: str
    name: str
    status: str
    version: str
    stage: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        project=settings.project,
        name=settings.name,
        status="ok",
        version=settings.version,
        stage=settings.stage,
    )
