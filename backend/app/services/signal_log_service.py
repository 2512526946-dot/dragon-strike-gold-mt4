from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.schemas.signal import PlaceholderSignal
from app.schemas.signal_log import SignalLogEntry


class SignalLogService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def save_placeholder_signal(self, signal: PlaceholderSignal) -> SignalLogEntry:
        created_at = datetime.now(timezone.utc)
        entry = SignalLogEntry(
            log_id=f"log-{created_at.strftime('%Y%m%d%H%M%S%f')}",
            created_at=created_at,
            log_type="placeholder_signal",
            source="placeholder",
            symbol=signal.symbol,
            signal_id=signal.signal_id,
            action=signal.action,
            signal_type=signal.signal_type,
            lifecycle_status=signal.lifecycle_status,
            is_placeholder=True,
            is_tradable=False,
            final_score=0,
            suggested_lot=0,
            allow_chasing=False,
        )
        log_path = self._log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as file:
            file.write(entry.model_dump_json() + "\n")
        return entry

    def _log_path(self) -> Path:
        log_dir = Path(self._settings.signal_log_dir)
        if not log_dir.is_absolute():
            project_root = Path(__file__).resolve().parents[3]
            log_dir = project_root / log_dir
        return log_dir / self._settings.placeholder_signal_log_file
