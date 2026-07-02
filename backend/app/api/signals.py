from fastapi import APIRouter

from app.config import get_settings
from app.schemas.signal import PlaceholderSignal
from app.services.placeholder_signal_service import PlaceholderSignalService

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/placeholder", response_model=PlaceholderSignal)
def get_placeholder_signal() -> PlaceholderSignal:
    service = PlaceholderSignalService(get_settings())
    return service.get_placeholder()
