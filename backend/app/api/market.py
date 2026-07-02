from fastapi import APIRouter

from app.config import get_settings
from app.schemas.market import MarketSnapshot
from app.services.mock_market_service import MockMarketService

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/snapshot", response_model=MarketSnapshot)
def get_market_snapshot() -> MarketSnapshot:
    service = MockMarketService(get_settings())
    return service.get_snapshot()
