# account_snapshot.json Format

`account_snapshot.json` is the planned file format for a future MT4 read-only file bridge output. It captures aggregate account state for future risk controls, safety checks, and review workflows.

This document does not define an MT4 EA implementation, MQL4 code, backend reader, trading strategy, risk calculation code, position sizing code, GoLiveGate implementation, machine learning workflow, agent workflow, or order workflow.

## File Purpose

- File type: `account_snapshot`
- Suggested path: `data/mt4/account_snapshot.json`
- Producer: future MT4 read-only EA that exports aggregate account status only.
- Consumer: future backend file reader, not implemented in this work item.
- Scope: account-level status needed for future safety checks.

The file is read-only input. It must not contain account passwords, API keys, real account numbers, real orders, position details, automatic trading instructions, or buy/sell recommendations.

Future 1% single-trade risk checks, 3% daily loss checks, no-overnight checks, position suggestions, and GoLiveGate may depend on this file. This work item only defines the format; it does not implement those calculations or decisions.

## Write Pattern

To avoid the backend reading a half-written file, the future MT4 file bridge should write in two steps:

1. Write the full payload to `data/mt4/account_snapshot.tmp`.
2. Flush and close the temporary file.
3. Atomically replace `data/mt4/account_snapshot.json` with the completed temporary file.

The backend should treat a partially written file, invalid JSON, or stale timestamp as unusable account data when reader logic is implemented later.

## Update Frequency

The first version can update every 5 seconds, or whenever account equity, margin, or free margin changes. Millisecond-level updates are not required for this project.

## Privacy And Safety

- Do not output account passwords.
- Do not output API keys.
- Do not output real account numbers.
- Do not output order details.
- Do not output position details.
- Output only aggregated account state needed for future risk controls.
- `account_identifier` must remain masked or omitted in examples and docs.

## Example

See [account_snapshot.example.json](./account_snapshot.example.json).

## Fields

| Field | Required | Rule |
| --- | --- | --- |
| `schema_version` | Yes | Current format version, starting at `1.0`. |
| `file_type` | Yes | Must be `account_snapshot`. |
| `source` | Yes | Must be `mt4_file_bridge`. |
| `environment` | Yes | Use `demo_or_live_unknown` until environment detection is defined. |
| `generated_at` | Yes | File generation timestamp; must not be empty. |
| `local_time` | Yes | Local machine timestamp with timezone offset. |
| `account_currency` | Yes | Example uses `USD`; must not be empty. |
| `account_mode` | Yes | Use `demo_or_live_unknown` until mode detection is defined. |
| `account_identifier` | Yes | Must be `masked_or_omitted`; never write a real account number. |
| `balance` | Yes | Account balance; should not be negative. |
| `equity` | Yes | Account equity; should not be negative. |
| `credit` | Yes | Account credit, if available. |
| `margin` | Yes | Current used margin; should not be negative. |
| `free_margin` | Yes | Current free margin; should not be negative. |
| `margin_level_pct` | Yes | Margin level percent; use `null` when there is no margin usage. |
| `daily_realized_pnl` | Yes | Current-day realized PnL snapshot. |
| `daily_unrealized_pnl` | Yes | Current-day unrealized PnL snapshot. |
| `daily_total_pnl` | Yes | Sum of realized and unrealized daily PnL. |
| `daily_loss_pct` | Yes | Current-day loss percent; should not be negative. |
| `risk_limits` | Yes | Object describing project risk guardrails. |
| `open_position_count` | Yes | Aggregate count only; should not be negative. |
| `pending_order_count` | Yes | Aggregate count only; should not be negative. |
| `has_open_positions` | Yes | Boolean summary flag only. |
| `has_pending_orders` | Yes | Boolean summary flag only. |
| `is_tradable` | Yes | Must be `false`; this file itself is not a trading permission. |
| `snapshot_quality` | Yes | Example uses `example_only`. |
| `note` | Yes | Must clearly state that the snapshot is not a trading signal or permission. |

## Risk Limits Object

`risk_limits` must contain:

| Field | Required | Rule |
| --- | --- | --- |
| `max_single_trade_loss_pct` | Yes | Example value is `1.0`. |
| `max_daily_loss_pct` | Yes | Example value is `3.0`. |
| `no_overnight` | Yes | Example value is `true`. |
| `primary_session` | Yes | Example value is `Asia`. |

These values are documented project guardrails only. This work item does not implement risk calculation, position sizing, signal blocking, or GoLiveGate.

## Future Use

This file may support future safety checks, including:

- Reading account equity.
- Calculating the maximum loss amount for a 1% single-trade risk limit.
- Checking whether daily loss is approaching the 3% limit.
- Deciding whether new signals should be paused.
- Supporting future position suggestions.
- Supporting future GoLiveGate checks.
- Supporting future no-overnight checks.

These are planning notes only. No risk calculation, position sizing, strategy, signal blocking, or trade action is implemented in this work item.

## Data Quality Requirements

- `account_currency` must not be empty.
- `balance` should not be negative.
- `equity` should not be negative.
- `free_margin` should not be negative.
- `daily_loss_pct` should not be negative.
- `open_position_count` should not be negative.
- `pending_order_count` should not be negative.
- Stale files must be treated as expired account snapshot data by future backend logic.
- Invalid JSON must not be used as account data.

## Safety Boundary

This format is read-only and analysis-only.

- It must not place orders.
- It must not close positions.
- It must not modify orders or protective levels.
- It must not include account passwords.
- It must not include API keys.
- It must not include real account numbers.
- It must not include order details.
- It must not include position details.
- It must not include trading recommendations.
- It must not include automatic trading instructions.
- `account_snapshot` does not mean the system allows trading.

The JSON schema must not include fields named `password`, `account_password`, `api_key`, `position_detail`, `ticket`, `OrderSend`, `OrderClose`, `OrderModify`, or `OrderDelete`.

The JSON values must not include trading action values such as `buy`, `sell`, `long`, `short`, `open_position`, or `close_position`.
