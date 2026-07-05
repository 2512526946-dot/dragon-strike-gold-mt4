from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.demo_readonly import router as demo_readonly_router
from app.api.health import router as health_router
from app.api.market import router as market_router
from app.api.mt4 import router as mt4_router
from app.api.signals import router as signals_router
from app.config import get_settings
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.project,
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(demo_readonly_router)
app.include_router(health_router)
app.include_router(market_router)
app.include_router(mt4_router)
app.include_router(signals_router)
