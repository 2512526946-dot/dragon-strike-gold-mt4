# Decisions

This file is one of the current project decision entry points for 巨龙出击 / `dragon-strike-gold-mt4`. It records design decisions only. It is not an execution policy for current code.

## MT4 Demo Account Training Decisions

The following decisions are now part of the project direction:

- First stage is demo-only.
- Real-money trading is outside the current phase.
- The agent cannot freely place orders.
- The first version prioritizes read-only data and semi-automatic confirmation.
- Automatic demo trading is delayed and off by default.
- Every future demo execution must pass DataQualityGate, RiskGate, PositionSizing, and ExecutionGate.
- Martingale position adding is not allowed.
- Grid position adding is not allowed.
- Overnight holding is not allowed.
- No stop-loss price means no execution.
- No account equity means no execution.
- Stale data means no execution.
- Failed risk checks mean no execution.
- Account passwords and login credentials must not be saved.
- The agent cannot modify risk rules.
- The agent cannot directly call the EA to place orders.

These decisions apply to future demo-account training only. They do not enable execution in the current system.
