# MT4 File Bridge Format Overview

This directory documents the planned file formats for the future MT4 read-only file bridge. The bridge is intended to export structured JSON snapshots from MT4 into `data/mt4/` so the backend can later read market and account context.

This document does not define an MT4 EA implementation, MQL4 code, backend reader, frontend behavior, trading strategy, risk calculation code, position sizing code, GoLiveGate implementation, machine learning workflow, agent workflow, or order workflow.

## Files

| File | Planned path | Purpose |
| --- | --- | --- |
| `live_tick.json` | `data/mt4/live_tick.json` | Real-time tick snapshot for `XAUUSD`, including bid, ask, spread, timestamp, digits, and point size. |
| `latest_bars.json` | `data/mt4/latest_bars.json` | Recent candle snapshots for `M15`, `H1`, `H4`, and `D1`. |
| `symbol_spec.json` | `data/mt4/symbol_spec.json` | Broker-reported symbol specifications, point value inputs, lot constraints, margin data, and spread details. |
| `account_snapshot.json` | `data/mt4/account_snapshot.json` | Aggregate account state for future safety checks, including equity, margin, daily loss status, and documented risk guardrails. |

All four files are data inputs only. They do not mean the system allows trading, and they must not be treated as trading recommendations.

## Write Pattern

The future MT4 read-only exporter should use a temporary-file write pattern for every bridge file:

1. Write the complete payload to the matching `.tmp` file, such as `data/mt4/live_tick.tmp`.
2. Flush and close the temporary file.
3. Atomically replace the matching `.json` file, such as `data/mt4/live_tick.json`.

The future backend reader should read only the `.json` files. This pattern avoids reading half-written JSON while MT4 is updating the files.

## Recommended Update Frequency

| File | Suggested refresh behavior |
| --- | --- |
| `live_tick.json` | On each MT4 tick or about once per second. |
| `latest_bars.json` | About once every 5 seconds or when a new candle is formed. |
| `symbol_spec.json` | When the EA starts, with optional low-frequency refresh later. |
| `account_snapshot.json` | About once every 5 seconds, or when equity, margin, or free margin changes. |

The project is designed for steady gold decision support on H1/M15 workflows. Millisecond-level file updates are not required for the first bridge version.

## Future Backend Read Order

When backend file reading is implemented later, the recommended validation order is:

1. Check whether the expected file exists.
2. Check whether the file contains valid JSON.
3. Check `schema_version` and `file_type`.
4. Check freshness using `generated_at` or `server_time`.
5. Check field quality, including required fields, numeric bounds, non-empty symbol values, and expected source values.
6. If data quality is stale or invalid, route the state into a future `DataQualityGate` and block any trading-signal workflow.

This work item only documents the future read order. It does not implement backend file reading or `DataQualityGate`.

## Relationship To Future Modules

- `live_tick.json` and `latest_bars.json` are future inputs for market analysis, display, and data quality checks.
- `symbol_spec.json` is a future input for point value checks, lot constraints, spread checks, margin checks, and position sizing.
- `account_snapshot.json` is a future input for account equity checks, 1% single-trade risk checks, 3% daily loss checks, no-overnight checks, and GoLiveGate.
- All four files are read-only data inputs. They do not equal system permission to trade.

## Safety Boundary

The MT4 file bridge must remain read-only in the first phase.

The bridge must not:

- Place orders.
- Close positions.
- Modify orders or protective levels.
- Include account passwords.
- Include API keys.
- Include real account numbers.
- Include real order details.
- Include position details.
- Include trading recommendations.
- Include automatic trading instructions.
- Include `OrderSend`, `OrderClose`, `OrderModify`, or `OrderDelete` as executable behavior.

The bridge files must not contain action values such as `buy`, `sell`, `long`, `short`, `open_position`, or `close_position`.

## Development Roadmap

The current 1A phase defines file formats only. A conservative future path is:

1. `1B`: backend reader for MT4 bridge files.
2. `1C`: data quality gate for stale, missing, malformed, or unsafe file states.
3. `1D`: MT4 read-only EA that outputs the documented files.
4. `2A`: 10x risk controls and position sizing calculations.
5. Later phases: signal workflow, review workflow, agent workflow, machine learning experiments, and any go-live planning.

Automatic trading remains forbidden in the first phase.
