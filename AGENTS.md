# 巨龙出击仓库规则

本文件定义仓库内所有 Codex 任务长期适用的公共边界。具体工单可以收紧范围，但不得绕过这些规则。

## 1. 项目定位

- 项目代号：巨龙出击。
- 仓库：`dragon-strike-gold-mt4`。
- 平台：TradeMax Global MT4 Demo。
- Canonical 品种：XAUUSD。
- Broker symbol 示例：GOLD。
- 当前默认：Demo-only / Read-only。
- 当前下单责任：用户本人。
- 当前系统权限：只读分析和建议，不允许自动下单。
- 当前不是自动实盘交易系统。
- 上述平台定位不代表当前已经接入真实 MT4 或真实账户。
- 当前目标是构建智能副驾驶、数据质量、风险教练、仓位助手和复盘训练底座。

## 2. 权限模型

- Agent / LLM 只有分析、解释和建议权。
- 程序 Gate 拥有否决权。
- Writer 只能提供事实数据。
- EA 只有在未来获得单独批准后，才可能拥有受限执行权。
- 当前没有交易或执行权限。
- 未来半自动阶段也必须由用户确认。

## 3. 永久安全红线

默认禁止：

- 实盘交易；
- 自动下单；
- 调用 EA；
- MQL4 交易执行；
- 马丁策略；
- 网格策略；
- 无止损交易；
- 隔夜持仓；
- client 修改 source mode；
- client 修改 freshness；
- client 修改文件大小政策；
- writer 修改 server policy；
- stale、malformed 或 mixed-generation 数据进入分析；
- 任一 Gate 拒绝后继续处理；
- 将 readiness 解释为交易许可；
- 将 DataQualityGate 解释为交易许可。

## 4. Facts 与 Policy 分离

Writer 只提供：

- 行情事实；
- 账户事实；
- bundle identity；
- 固定安全 envelope。

Server-side policy 包括：

- freshness；
- future skew；
- 文件大小；
- 风险比例；
- 交易时段；
- 不隔夜；
- 杠杆约束；
- 所有 Gates。

Writer、manifest、payload 和 client 均不得覆盖 server policy。

## 已批准的交易与风险政策

- 杠杆上限：10 倍；
- 单笔最大允许亏损：账户权益的 1%；
- 单日最大允许亏损：账户权益的 3%；
- 主要计划交易时段：亚洲时段；
- 不允许隔夜持仓；
- 必须先经过模拟盘训练；
- 当前所有交易由用户手动确认和下单；
- 当前不允许自动下单；
- DataQualityGate 未通过时不得进入分析；
- GoLiveGate 未通过时不得升级到任何实盘阶段。

以上是已经批准的 server-side policy 和未来验收约束，不代表当前代码已经完整实现这些 Gate，也不代表系统已获得交易或执行许可。

Writer、manifest、payload 和 client 均不得覆盖这些政策。

## 5. 工单和 Git 纪律

- 一次只执行一个工单。
- 所有任务开始前先核对 Git checkpoint。
- 开发、review、merge、release 必须分离。
- 开发工单不 merge；review 不修改工作树；merge 不开发；release 不开发。
- 不得自动进入下一工单或自动调用下一个写操作 Skill。
- 不得同时创建平行开发分支。
- 存在未合并分支时，先 review、修订或 merge。
- 工作区不干净时停止。
- 不 stash、不删除、不覆盖用户修改。
- 不 amend，除非工单明确允许。
- 不 force push。
- 默认只允许 fast-forward merge。
- 普通小工单不创建 tag。
- 不得删除工作分支，除非用户明确批准。
- 状态必须从 Git、ADR、协议、代码和测试重新确认，不得仅相信之前的回传摘要。

修订工单规则：

- 工单明确要求继续现有分支时，不得因为分支存在而停止。
- 只有工单要求创建新分支且目标分支已存在时才停止。

## 6. 测试纪律

- 先运行 targeted tests，再运行相关 regression。
- 生产代码变更通常运行完整 backend tests。
- frontend 变更运行 tests 和 build。
- 只允许已知 warning；新增 warning 必须调查并汇报。
- 测试失败时不得修改无关模块绕过。
- 回传的“全部通过”不能替代实际代码审查。

已知情况：

- `StarletteDeprecationWarning` 是既有 warning。
- Windows 环境可能无法创建 symlink，相关测试可以明确 skip。
- skipped 不代表生产 symlink 检查已被证明。

## 7. 输出安全

不得在结果、日志或报告中暴露敏感信息：

- 密码、token 或凭证；
- 真实账户号；
- 本地绝对路径；
- raw payload；
- 不必要的价格和余额；
- traceback 或异常原文；
- checksum。

### 允许的只读建议

- 行情与趋势分析；
- 风险提示；
- 情景分析；
- 机会候选；
- 失效条件；
- 止损距离分析；
- 建议仓位范围；
- 复盘和训练反馈。

这些输出必须明确标记为非执行性建议，不代表交易许可，不代表 Gate 已通过，也不得自动转化为订单。

### 禁止输出

- 可直接执行的订单指令；
- 下单 payload；
- 自动买卖命令；
- EA 调用指令；
- 将分析包装成交易许可；
- 将 readiness、DataQualityGate 或 GoLiveGate 包装成执行许可；
- 绕过用户确认的交易动作。

不得放宽 Demo-only、Read-only 和无自动下单边界。

## 8. 模型选择

以下任务开始前必须明确输出：

`模型要求：Codex Pro`

如果界面没有独立 Pro 标签，则使用当前可用的最高推理强度。

必须使用上述要求的任务：

- 仓库级架构决策；
- canonical protocol 变更；
- 第一版 production validator、reader 或 writer；
- API reader activation；
- Settings 和 source mode 关键接入；
- Windows filesystem security；
- MT4 / MQL4；
- DataQualityGate 关键集成；
- Agent / RiskGate / PositionSizing；
- TradePlanSchema；
- ExecutionGate；
- EA 或任何执行链。

普通高强度模式可以处理：

- 明确的小修订；
- tests-only；
- docs-only；
- 通过验收后的 ff-only merge；
- 用户已批准的 tag。

## 9. 任务结束汇报

每个任务必须说明：

- 任务名称；
- 起点 main；
- 当前分支；
- commit；
- 修改文件；
- 测试；
- warning / skipped；
- 边界检查；
- 是否 push；
- 是否 merge；
- 是否 tag；
- 下一建议；
- 尚未实现能力。
