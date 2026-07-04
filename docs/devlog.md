# Devlog

This file is one of the current project documentation entry points for 巨龙出击 / `dragon-strike-gold-mt4`. It records current design direction only. It is not a trading signal, not trading permission, and not proof that the system can connect to MT4 or execute orders.

## MT4 Demo Account Training Direction

The project now includes MT4 demo account training as a documented future direction.

Current scope:

- This direction is documentation-only.
- The project does not connect to any MT4 account in this phase.
- The project does not save account passwords or login credentials.
- The project does not write an MT4 EA or MQL4 code in this phase.
- The project does not open, close, modify, or delete orders.
- The project does not expose live or demo execution in the current code.

The first implementation stages must be demo-only and read-only first. Semi-automatic demo confirmation can come later, and automatic demo training must be delayed, explicitly enabled, and off by default. Real-money trading is outside the current phase.

The purpose of this direction is to improve:

- Training efficiency.
- Review quality.
- Demo account execution data and agent judgment data accumulation.
- Validation of DataQualityGate / RiskGate / PositionSizing / ExecutionGate behavior.

The long-term execution chain must be controlled:

```text
Agent proposes a trade plan
  -> DataQualityGate
  -> RiskGate
  -> PositionSizing
  -> ExecutionGate
  -> user confirmation or later AutoDemoTrainingMode
  -> MT4 EA on demo account only
  -> ExecutionAuditLog
  -> observation / paper review / manual execution / demo execution review
```

The agent has recommendation authority only. Risk and execution gates have veto authority.
