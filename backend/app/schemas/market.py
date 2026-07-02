from datetime import datetime

from pydantic import BaseModel, Field


class MarketSnapshot(BaseModel):
    symbol: str
    source: str
    timestamp: datetime
    bid: float
    ask: float
    spread: float
    spread_points: int
    digits: int
    data_status: str
    is_mock: bool
    is_tradable: bool
    note: str = Field(
        default="Mock market data for development only. Not a trading signal."
    )
