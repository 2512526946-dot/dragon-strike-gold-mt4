# 巨龙出击开发者日志

项目：巨龙出击 / dragon-strike-gold-mt4

本文记录当前开发阶段、已确认的产品方向和后续顺序。它是开发者日志和架构决策索引，不是交易建议，也不代表系统具备真实交易能力。

## 当前阶段状态

当前 main 已完成到 G36：合并 1C-6 到 main 并推送 GitHub。

当前 main commit：

```text
9bc2367b13fde81fdd962e20f47a35e24b901daf
```

已完成阶段：

- 1A：MT4 文件格式规划阶段，tag 为 `v0.5.0-mt4-file-format-planning`
- 1B：后端 MT4 文件只读读取链路阶段，tag 为 `v0.6.0-mt4-read-pipeline`
- 1C：DataQualityGate 核心代码阶段已完成并合并到 main

1C 已进入 main 的内容：

- 1C-1：DataQualityGate v0 聚合结果层
- 1C-2：MT4 四文件最小业务字段存在性检查层
- 1C-3：MT4 四文件最小字段类型检查层
- 1C-4：MT4 四文件最小数值范围检查层
- 1C-5：MT4 四文件最小跨字段关系检查层
- 1C-6：DataQualityGate v1 最终汇总层

阶段 tag `v0.7.0-data-quality-gate` 尚未创建。

## 产品最终形态

巨龙出击未来主形态确定为：

```text
本地网页控制台 + MT4 只读桥接 EA + 人工下单
```

它不是手机 App 优先，不是完整嵌入 MT4 的复杂插件，也不是自动交易机器人。

未来运行结构：

```text
TradeMax Global MT4 Terminal
        ↓
只读 MT4 文件桥接 EA
        ↓
本地后端 FastAPI
        ↓
巨龙出击网页控制台
        ↓
用户人工决策、人工下单
```

MT4 的职责：

- 提供 XAUUSD 行情
- 提供 K 线
- 提供品种规格
- 提供账户快照
- 保留人工下单入口

巨龙出击网页的职责：

- 数据质量检查
- 黄金多周期分析
- 风险闸门
- 仓位建议
- 观察信号记录
- 复盘
- 智能体解释
- 纪律监督

后续可以包装为 Windows 桌面程序，例如 `巨龙出击.exe`，但底层仍然是本地网页前端、本地后端和 MT4 文件桥接。

## 当前绝对禁止事项

当前阶段禁止开发：

- MT4 EA
- MQL4 代码
- OrderSend
- OrderClose
- OrderModify
- OrderDelete
- 真实 MT4 接入
- 真实行情接入
- 真实账户读取
- 真实下单
- 自动交易
- 交易策略
- 风控计算
- 仓位计算
- GoLiveGate
- AutoTradeGate
- 智能体代码
- 机器学习

当前阶段可以继续做：

- 文档整理
- DataQualityGate 合并
- 阶段 tag
- 只读诊断接口规划
- 观察信号结构规划
- 复盘日志结构规划

## 文档索引

- `docs/architecture_decisions.md`：产品形态、架构边界、QuantDinger 借鉴边界
- `docs/ui_design_principles.md`：首页信息优先级、界面布局和颜色原则
- `docs/agent_architecture.md`：未来多智能体分工与智能体经理原则
- `docs/review_and_execution_policy.md`：观察信号、纸面复盘、人工执行复盘和仓位设计原则
- `docs/autotrade_long_term_policy.md`：长期自动交易路线和 AutoTradeGate 边界

## 后续建议顺序

1. 执行 docs-only 工单并本地提交本文档集合。
2. 创建并推送 `v0.7.0-data-quality-gate` 阶段性 tag。
3. 继续 1D 或后续只读诊断规划，仍保持不接真实 MT4、不做自动交易。
