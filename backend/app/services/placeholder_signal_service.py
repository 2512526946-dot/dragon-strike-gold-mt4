from datetime import datetime, timezone

from app.config import Settings
from app.schemas.signal import EntryZone, PlaceholderSignal


class PlaceholderSignalService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_placeholder(self) -> PlaceholderSignal:
        created_at = datetime.now(timezone.utc)
        signal_id = f"placeholder-{created_at.strftime('%Y%m%d%H%M%S')}"

        return PlaceholderSignal(
            signal_id=signal_id,
            symbol=self._settings.default_symbol,
            source="placeholder",
            timestamp=created_at,
            action="observe_only",
            signal_type="placeholder_only",
            lifecycle_status="CREATED",
            market_regime="unknown",
            final_score=0,
            entry_zone=EntryZone(),
            confirm_condition="No real confirmation condition. Placeholder only.",
            stop_loss=None,
            take_profit_1=None,
            take_profit_2=None,
            invalidation_condition="N/A",
            allow_chasing=False,
            risk_level="none",
            leverage_10x_status="not_evaluated",
            suggested_lot=0,
            is_placeholder=True,
            is_tradable=False,
        )
