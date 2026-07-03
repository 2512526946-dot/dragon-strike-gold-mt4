from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.mt4_file_reader import Mt4JsonReadResult, read_json_object_file


LIVE_TICK_FILE = "live_tick.json"
LATEST_BARS_FILE = "latest_bars.json"
SYMBOL_SPEC_FILE = "symbol_spec.json"
ACCOUNT_SNAPSHOT_FILE = "account_snapshot.json"


@dataclass(frozen=True)
class Mt4SnapshotReadResult:
    live_tick: Mt4JsonReadResult
    latest_bars: Mt4JsonReadResult
    symbol_spec: Mt4JsonReadResult
    account_snapshot: Mt4JsonReadResult


def read_mt4_snapshot_files(base_dir: Path | str) -> Mt4SnapshotReadResult:
    root = Path(base_dir)

    return Mt4SnapshotReadResult(
        live_tick=read_json_object_file(root / LIVE_TICK_FILE),
        latest_bars=read_json_object_file(root / LATEST_BARS_FILE),
        symbol_spec=read_json_object_file(root / SYMBOL_SPEC_FILE),
        account_snapshot=read_json_object_file(root / ACCOUNT_SNAPSHOT_FILE),
    )
