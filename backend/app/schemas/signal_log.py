from datetime import datetime

from pydantic import BaseModel, Field


class SignalLogEntry(BaseModel):
    log_id: str
    created_at: datetime
    log_type: str
    source: str
    symbol: str
    signal_id: str
    action: str
    signal_type: str
    lifecycle_status: str
    is_placeholder: bool
    is_tradable: bool
    final_score: int
    suggested_lot: int
    allow_chasing: bool
    note: str = Field(
        default="Placeholder signal log for development only. Not a trading recommendation."
    )


class SignalLogResponse(SignalLogEntry):
    logged: bool
