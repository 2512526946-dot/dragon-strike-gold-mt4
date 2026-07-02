from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.market import router as market_router
from app.api.signals import router as signals_router
from app.config import get_settings
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.project,
    version=settings.version,
)
app.include_router(health_router)
app.include_router(market_router)
app.include_router(signals_router)
