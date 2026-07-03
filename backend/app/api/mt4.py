from datetime import UTC, datetime

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.mt4_diagnostics import (
    Mt4DiagnosticsResponse,
    mt4_diagnostics_response,
)
from app.services.mt4_diagnostics import build_mt4_diagnostics

router = APIRouter(prefix="/api/mt4", tags=["mt4"])


@router.get("/diagnostics", response_model=Mt4DiagnosticsResponse)
def get_mt4_diagnostics() -> Mt4DiagnosticsResponse:
    settings = get_settings()
    diagnostics = build_mt4_diagnostics(
        settings.mt4_data_path,
        datetime.now(UTC),
    )
    return mt4_diagnostics_response(diagnostics)
