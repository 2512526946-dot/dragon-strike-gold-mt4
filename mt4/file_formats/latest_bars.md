# latest_bars.json Format

`latest_bars.json` is the planned file format for a future MT4 read-only file bridge output. It is only a recent candle snapshot for analysis display, data checks, and later review workflows.

This document does not define an MT4 EA implementation, MQL4 code, backend reader, trading strategy, risk engine, machine learning workflow, agent workflow, or order workflow.

## File Purpose

- File type: `latest_bars`
- Suggested path: `data/mt4/latest_bars.json`
- Producer: future MT4 read-only EA that exports candle snapshots only.
- Consumer: future backend file reader, not implemented in this work item.
- Scope: recent bars for `XAUUSD` across selected analysis timeframes.

The file must not contain account passwords, API keys, account snapshots, real orders, automatic trading instructions, or buy/sell recommendations.

## Write Pattern

To avoid the backend reading a half-written file, the future MT4 file bridge should write in two steps:

1. Write the full payload to `data/mt4/latest_bars.tmp`.
2. Flush and close the temporary file.
3. Atomically replace `data/mt4/latest_bars.json` with the completed temporary file.

The backend should treat a partially written file, invalid JSON, or stale timestamp as unusable bar data when reader logic is implemented later.

## Recommended Timeframes

- `M15`: entry confirmation timeframe.
- `H1`: primary opportunity timeframe.
- `H4`: higher-timeframe direction context.
- `D1`: daily direction context.

The first version should include at least `M15`, `H1`, `H4`, and `D1`.

## Update Frequency

The first version can update once every 5 seconds or whenever a new candle is formed. This project is designed for steadier decision support on H1/M15 workflows, so millisecond-level refresh is not required.

## Example

See [latest_bars.example.json](./latest_bars.example.json).

## Top-Level Fields

| Field | Required | Rule |
| --- | --- | --- |
| `schema_version` | Yes | Current format version, starting at `1.0`. |
| `file_type` | Yes | Must be `latest_bars`. |
| `source` | Yes | Must be `mt4_file_bridge`. |
| `environment` | Yes | Use `demo_or_live_unknown` until environment detection is defined. |
| `symbol` | Yes | Example defaults to `XAUUSD`; must not be empty. |
| `generated_at` | Yes | File generation timestamp; must not be empty. |
| `local_time` | Yes | Local machine timestamp with timezone offset. |
| `is_tradable` | Yes | Must be `false`; this file is not a permission to trade. |
| `timeframes` | Yes | Object containing at least `M15`, `H1`, `H4`, and `D1`. |
| `note` | Yes | Must clearly state that the snapshot is not a trading signal. |

Future backend logic should reject or mark the file as delayed when `generated_at` is too old for the configured freshness threshold.

## Timeframe Object

Each timeframe object must contain:

| Field | Required | Rule |
| --- | --- | --- |
| `timeframe` | Yes | Must match the key, such as `M15`, `H1`, `H4`, or `D1`. |
| `bar_count` | Yes | Number of bars exported for that timeframe. |
| `bars` | Yes | Array of bar objects. |

Bars should be sorted in ascending time order, oldest first. If a future exporter chooses descending order, it must document that change in a new schema version.

## Bar Object

Each bar in `bars` must contain:

| Field | Required | Rule |
| --- | --- | --- |
| `time` | Yes | Bar open time in ISO 8601 format. |
| `open` | Yes | Numeric open price. |
| `high` | Yes | Must be greater than or equal to `open`, `close`, and `low`. |
| `low` | Yes | Must be less than or equal to `open`, `close`, and `high`. |
| `close` | Yes | Numeric close price; must not be empty. |
| `tick_volume` | Yes | Must be greater than or equal to `0`. |
| `spread` | Yes | Spread snapshot for the bar, if available. |
| `real_volume` | Yes | Use `0` when unavailable in MT4. |
| `is_closed` | Yes | `true` for closed bars; `false` may be used for the currently forming bar. |

## Data Quality Requirements

- `generated_at` must not be empty.
- `symbol` must exist and must not be empty.
- `timeframes` must exist.
- Required timeframes: `M15`, `H1`, `H4`, and `D1`.
- Bars must be sorted in ascending time order, oldest first.
- `high` must be greater than or equal to `open`, `close`, and `low`.
- `low` must be less than or equal to `open`, `close`, and `high`.
- `close` must not be empty.
- `tick_volume` must not be negative.
- Stale files must be treated as delayed data by future backend logic.
- Invalid JSON must not be used as bar data.

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
