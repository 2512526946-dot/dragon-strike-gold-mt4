from datetime import datetime, timezone

from app.config import Settings
from app.schemas.market import MarketSnapshot


class MockMarketService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_snapshot(self) -> MarketSnapshot:
        digits = self._settings.mock_digits
        bid = round(self._settings.mock_initial_price, digits)
        ask = round(bid + self._settings.mock_spread, digits)
        spread = round(ask - bid, digits)
        spread_points = int(round(spread * (10**digits)))

        return MarketSnapshot(
            symbol=self._settings.default_symbol,
            source="mock",
            timestamp=datetime.now(timezone.utc),
            bid=bid,
            ask=ask,
            spread=spread,
            spread_points=spread_points,
            digits=digits,
            data_status="mock_ok",
            is_mock=True,
            is_tradable=False,
        )
