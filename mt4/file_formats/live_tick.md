# live_tick.json Format

`live_tick.json` is the planned file format for a future MT4 read-only file bridge output. It is only a market tick snapshot for analysis display and later validation work.

This document does not define an MT4 EA implementation, MQL4 code, backend reader, trading strategy, risk engine, or order workflow.

## File Purpose

- File type: `live_tick`
- Suggested path: `data/mt4/live_tick.json`
- Producer: future MT4 read-only EA that exports quote snapshots only.
- Consumer: future backend file reader, not implemented in this work item.
- Scope: one current quote snapshot for `XAUUSD`.

The file must not contain account passwords, API keys, account snapshots, real orders, automatic trading instructions, or buy/sell recommendations.

## Write Pattern

To avoid the backend reading a half-written file, the future MT4 file bridge should write in two steps:

1. Write the full payload to `data/mt4/live_tick.tmp`.
2. Flush and close the temporary file.
3. Atomically replace `data/mt4/live_tick.json` with the completed temporary file.

The backend should treat a partially written file, invalid JSON, or stale timestamp as unusable market data when reader logic is implemented later.

## Update Frequency

The first version can update once per second or on each MT4 tick. This project is designed for steadier decision support on higher timeframes, so high-frequency millisecond updates are not required.

## Example

See [live_tick.example.json](./live_tick.example.json).

```json
{
  "schema_version": "1.0",
  "file_type": "live_tick",
  "source": "mt4_file_bridge",
  "environment": "demo_or_live_unknown",
  "symbol": "XAUUSD",
  "server_time": "2026-07-03T10:15:30Z",
  "local_time": "2026-07-03T18:15:30+08:00",
  "bid": 2030.12,
  "ask": 2030.42,
  "spread": 0.3,
  "spread_points": 30,
  "digits": 2,
  "point": 0.01,
  "tick_time_msc": 1783073730000,
  "is_tradable": false,
  "note": "MT4 live tick snapshot for analysis only. Not a trading signal."
}
```

## Field Rules

| Field | Required | Rule |
| --- | --- | --- |
| `schema_version` | Yes | Current format version, starting at `1.0`. |
| `file_type` | Yes | Must be `live_tick`. |
| `source` | Yes | Must be `mt4_file_bridge`. |
| `environment` | Yes | Use `demo_or_live_unknown` until environment detection is defined. |
| `symbol` | Yes | Example defaults to `XAUUSD`; must not be empty. |
| `server_time` | Yes | MT4/server timestamp; must not be empty. |
| `local_time` | Yes | Local machine timestamp with timezone offset. |
| `bid` | Yes | Numeric bid price; must be less than `ask`. |
| `ask` | Yes | Numeric ask price; must be greater than `bid`. |
| `spread` | Yes | `ask - bid`; must be greater than or equal to `0`. |
| `spread_points` | Yes | Spread expressed in points using `point`. |
| `digits` | Yes | Symbol precision from MT4. |
| `point` | Yes | Symbol point size from MT4. |
| `tick_time_msc` | Yes | Tick timestamp in milliseconds when available. |
| `is_tradable` | Yes | Must be `false`; this file is not a permission to trade. |
| `note` | Yes | Must clearly state that the snapshot is not a trading signal. |

Future backend logic should reject or mark the file as delayed when `server_time` is too old for the configured freshness threshold.

## Data Quality Requirements

- `server_time` must not be empty.
- `symbol` must exist and must not be empty.
- `bid` must be less than `ask`.
- `spread` must be greater than or equal to `0`.
- `digits` must exist.
- `point` must exist.
- Stale files must be treated as delayed data by future backend logic.
- Invalid JSON must not be used as market data.

## Safety Boundary

This format is read-only and analysis-only.

- It must not place orders.
- It must not close positions.
- It must not modify orders or protective levels.
- It must not include account passwords.
- It must not include account snapshots.
- It must not include trading recommendations.
- It must not include automatic trading instructions.

The JSON schema must not include fields named `order`, `position`, `password`, `account_password`, `api_key`, `OrderSend`, `OrderClose`, `OrderModify`, or `OrderDelete`.

The JSON values must not include trading action values such as `buy`, `sell`, `long`, `short`, `open_position`, or `close_position`.
