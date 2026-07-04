# Architecture

This file is one of the current architecture documentation entry points for 巨龙出击 / `dragon-strike-gold-mt4`. It summarizes the future demo-account training architecture while keeping the current implementation boundary clear.

## MT4 Demo Account Execution Chain

Future demo account training must follow a gated chain:

```text
智能体生成交易计划
↓
DataQualityGate 检查数据是否可靠
↓
RiskGate 检查是否允许交易
↓
PositionSizing 硬计算手数
↓
ExecutionGate 检查是否允许执行
↓
用户确认 / 或后期 AutoDemoTrainingMode 开启
↓
MT4 EA 在模拟账号执行
↓
ExecutionAuditLog 记录执行前检查、是否通过、是否执行、执行结果
↓
复盘数据进入 observation / paper review / manual execution / demo execution review 链路
```

## Execution Roles

- The agent is not the executor.
- The agent cannot bypass risk controls.
- RiskGate can veto any plan.
- PositionSizing must hard-calculate lot size from account equity, stop-loss distance, tick value, lot limits, and risk limits.
- ExecutionGate can veto any plan after all earlier checks.
- The EA only executes approved commands.
- DemoAccountMode must clearly show that the system is in demo-only mode.

## First Version Boundary

The first version must prioritize read-only demo account data and semi-automatic user confirmation. It must not directly open full automation.

Current phase does not implement:

- MT4 account connection.
- MT4 EA.
- MQL4 code.
- Execution API.
- Frontend confirmation button.
- RiskGate code.
- PositionSizing code.
- ExecutionGate code.
- AutoDemoTrainingMode code.
- Automatic trading.
- Real-money trading.
