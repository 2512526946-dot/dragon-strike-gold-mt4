from datetime import datetime

from pydantic import BaseModel, Field


class EntryZone(BaseModel):
    low: float | None = None
    high: float | None = None


class PlaceholderSignal(BaseModel):
    signal_id: str
    symbol: str
    source: str
    timestamp: datetime
    action: str
    signal_type: str
    lifecycle_status: str
    market_regime: str
    final_score: int
    entry_zone: EntryZone
    confirm_condition: str
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    invalidation_condition: str
    allow_chasing: bool
    risk_level: str
    leverage_10x_status: str
    suggested_lot: int
    is_placeholder: bool
    is_tradable: bool
    note: str = Field(
        default="Placeholder signal for development only. Not a trading recommendation."
    )
