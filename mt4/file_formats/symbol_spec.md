# symbol_spec.json Format

`symbol_spec.json` is the planned file format for a future MT4 read-only file bridge output. It captures symbol specification data for analysis, data quality checks, and later risk calculation work.

This document does not define an MT4 EA implementation, MQL4 code, backend reader, trading strategy, position sizing code, risk engine, machine learning workflow, agent workflow, or order workflow.

## File Purpose

- File type: `symbol_spec`
- Suggested path: `data/mt4/symbol_spec.json`
- Producer: future MT4 read-only EA that exports symbol specification snapshots only.
- Consumer: future backend file reader, not implemented in this work item.
- Scope: broker-reported specifications for `XAUUSD`.

The file is read-only input. It must not contain account passwords, API keys, account snapshots, real orders, automatic trading instructions, or buy/sell recommendations.

Future position sizing, 10x risk checks, minimum lot checks, spread cost calculations, and point value calculations may depend on this file. This work item only defines the format; it does not implement those calculations.

## Write Pattern

To avoid the backend reading a half-written file, the future MT4 file bridge should write in two steps:

1. Write the full payload to `data/mt4/symbol_spec.tmp`.
2. Flush and close the temporary file.
3. Atomically replace `data/mt4/symbol_spec.json` with the completed temporary file.

The backend should treat a partially written file, invalid JSON, or stale timestamp as unusable specification data when reader logic is implemented later.

## Update Frequency

The first version can write this file when the EA starts. Symbol specifications usually do not need per-second updates.

Some broker-reported values can change, including spread, margin requirements, stop level, and freeze level. A later read-only exporter may refresh this file periodically, but that behavior is not implemented in this work item.

## Field Sources

- `digits`, `point`, and `spread` should come from MT4 symbol properties.
- `tick_size`, `tick_value`, `lot_size`, `min_lot`, `lot_step`, and `max_lot` must use actual MT4 values in future exporter work.
- `stop_level_points`, `freeze_level_points`, and `margin_required_per_lot` must use broker-reported values when available.
- Do not hard-code traditional gold contract assumptions.
- Different brokers can publish different `XAUUSD` specifications.

## Example

See [symbol_spec.example.json](./symbol_spec.example.json).

## Fields

| Field | Required | Rule |
| --- | --- | --- |
| `schema_version` | Yes | Current format version, starting at `1.0`. |
| `file_type` | Yes | Must be `symbol_spec`. |
| `source` | Yes | Must be `mt4_file_bridge`. |
| `environment` | Yes | Use `demo_or_live_unknown` until environment detection is defined. |
| `symbol` | Yes | Example defaults to `XAUUSD`; must not be empty. |
| `generated_at` | Yes | File generation timestamp; must not be empty. |
| `local_time` | Yes | Local machine timestamp with timezone offset. |
| `digits` | Yes | Symbol precision from MT4. |
| `point` | Yes | Symbol point size from MT4. |
| `tick_size` | Yes | Minimum tick size; must be greater than `0`. |
| `tick_value` | Yes | Tick value per lot; must be greater than `0`. |
| `lot_size` | Yes | Contract size per lot. |
| `min_lot` | Yes | Broker minimum lot; must be greater than `0`. |
| `lot_step` | Yes | Broker lot increment; must be greater than `0`. |
| `max_lot` | Yes | Broker maximum lot; must be greater than or equal to `min_lot`. |
| `spread` | Recommended | Current spread in price units. |
| `spread_points` | Recommended | Current spread in points; must not be negative. |
| `stop_level_points` | Recommended | Broker stop level in points. |
| `freeze_level_points` | Recommended | Broker freeze level in points. |
| `margin_required_per_lot` | Recommended | Margin required for one lot, as reported by the broker. |
| `margin_currency` | Recommended | Margin currency, such as `USD`. |
| `profit_currency` | Recommended | Profit currency, such as `USD`. |
| `base_currency` | Recommended | Base currency, such as `XAU`. |
| `quote_currency` | Recommended | Quote currency, such as `USD`. |
| `swap_long` | Optional | Broker-reported long swap value; informational only. |
| `swap_short` | Optional | Broker-reported short swap value; informational only. |
| `trade_allowed_by_broker` | Yes | Broker symbol availability flag; not a system permission to trade. |
| `is_tradable` | Yes | Must be `false`; this file itself is not a trading permission. |
| `spec_quality` | Yes | Example uses `example_only`. |
| `note` | Yes | Must clearly state that the snapshot is not a trading signal. |

Future backend logic should reject or mark the file as stale when `generated_at` is too old for the configured freshness threshold.

## Future Use

This file may support future analysis and risk checks, including:

- Calculating stop-loss amount for one lot.
- Checking whether the minimum lot would exceed the 1% risk limit.
- Calculating suggested lot size.
- Estimating spread cost.
- Checking `stop_level_points` and `freeze_level_points`.
- Checking whether future 10x risk rules pass.

These are planning notes only. No risk calculation, position sizing, strategy, or trade action is implemented in this work item.

Future formula notes:

```text
loss_amount_per_1_lot =
abs(entry_price - stop_loss) / tick_size * tick_value

risk_allowed_lots =
account_equity * 1% / loss_amount_per_1_lot
```

The future suggested lot size will be decided by risk allowed lots, leverage limits, `min_lot`, `lot_step`, and `max_lot` together.

## Data Quality Requirements

- `symbol` must not be empty.
- `tick_size` must be greater than `0`.
- `tick_value` must be greater than `0`.
- `min_lot` must be greater than `0`.
- `lot_step` must be greater than `0`.
- `max_lot` must be greater than or equal to `min_lot`.
- `spread_points` should not be negative.
- Stale files must be treated as expired specification data by future backend logic.
- Invalid JSON must not be used as symbol specification data.

## Safety Boundary

This format is read-only and analysis-only.

- It must not place orders.
- It must not close positions.
- It must not modify orders or protective levels.
- It must not include account passwords.
- It must not include account snapshots.
- It must not include trading recommendations.
- It must not include automatic trading instructions.
- `trade_allowed_by_broker` does not mean the system allows trading.

The JSON schema must not include fields named `password`, `account_password`, `api_key`, `order`, `position`, `ticket`, `OrderSend`, `OrderClose`, `OrderModify`, or `OrderDelete`.

The JSON values must not include trading action values such as `buy`, `sell`, `long`, `short`, `open_position`, or `close_position`.
