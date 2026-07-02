from fastapi import APIRouter

from app.config import get_settings
from app.schemas.signal import PlaceholderSignal
from app.schemas.signal_log import SignalLogResponse
from app.services.placeholder_signal_service import PlaceholderSignalService
from app.services.signal_log_service import SignalLogService

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/placeholder", response_model=PlaceholderSignal)
def get_placeholder_signal() -> PlaceholderSignal:
    service = PlaceholderSignalService(get_settings())
    return service.get_placeholder()


@router.post("/placeholder/log", response_model=SignalLogResponse)
def log_placeholder_signal() -> SignalLogResponse:
    settings = get_settings()
    signal = PlaceholderSignalService(settings).get_placeholder()
    log_entry = SignalLogService(settings).save_placeholder_signal(signal)
    return SignalLogResponse(logged=True, **log_entry.model_dump())
