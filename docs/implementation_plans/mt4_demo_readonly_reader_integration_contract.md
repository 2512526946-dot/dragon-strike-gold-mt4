# MT4 Demo Readonly Reader Integration Contract

本文档定义未来 `MT4 demo readonly reader` 的集成契约。本文档只是 reader integration contract；当前 1V-1 工单只写文档，不实现 reader，不读取文件，不接 MT4，不新增 API，不接 Dashboard，不生成交易建议，不生成执行指令。

当前系统已经具备以下只读验证核心：

- `mt4_demo_readonly_path_guard.py`
- `mt4_demo_readonly_schema_validator.py`
- `mt4_demo_readonly_source_summary_adapter.py`

未来 reader 只能作为这些安全层前后的胶水层，不能绕过任何安全边界。

## 1. 目标说明

本文档的目标是约束未来 reader 如何安全地从显式配置目录读取三个 demo-only / read-only JSON 文件，并将其变成安全的 `DemoReadOnlySourceSummary`。

当前工单明确不做以下事项：

- 不实现 reader。
- 不读取文件。
- 不检查文件是否存在。
- 不接 MT4。
- 不新增 API。
- 不接 diagnostics API。
- 不接 explanation API。
- 不接 Dashboard。
- 不生成交易建议。
- 不生成执行指令。
- 不生成 EA 指令。
- 不生成 `TradePlan`。

本文档不能被解释为启用文件读取、启用 MT4 bridge、启用 API source mode、启用 Dashboard 展示、启用交易或启用执行能力。

## 2. 未来 reader 允许读取的文件

未来 reader 只能读取以下三个白名单 JSON 文件：

- `account_snapshot.json`
- `positions_order_history.json`
- `market_symbol.json`

未来 reader 不允许读取其他文件。尤其禁止：

- 不允许读取 `.env`。
- 不允许读取日志。
- 不允许读取数据库。
- 不允许读取任意 Desktop / Downloads / Documents 文件。
- 不允许递归扫描目录。
- 不允许自动搜索文件系统。
- 不允许读取 raw terminal export。
- 不允许读取真实账户文件。
- 不允许读取执行命令文件。
- 不允许读取 EA 命令文件。
- 不允许读取非 JSON 白名单文件。
- 不允许读取带路径穿越、绝对路径、隐藏文件名或双扩展名的输入。

未来若要扩展文件列表，必须另开工单，先更新本契约、PathGuard、filename whitelist、schema validator、source summary adapter、安全测试和人工验收清单。

## 3. 未来 reader 数据流

未来数据流必须固定为：

```text
configured_demo_readonly_base_dir
↓
PathGuard
↓
FilenameWhitelist
↓
Read only the 3 whitelisted JSON files
↓
JSON parse
↓
SchemaValidator
↓
SourceSummaryAdapter
↓
DemoReadOnlySourceSummary
↓
future Diagnostics API source mode
```

未来 reader 必须遵守：

- reader 不能绕过 PathGuard。
- reader 不能绕过 FilenameWhitelist。
- reader 不能绕过 SchemaValidator。
- reader 不能绕过 SourceSummaryAdapter。
- reader 不能把 raw payload 直接传给 API/UI。
- reader 不能直接进入 Dashboard。
- reader 不能生成交易建议。
- reader 不能生成执行指令。
- reader 不能调用 MT4。
- reader 不能调用 EA。
- reader 不能调用网络。
- reader 不能调用交易执行模块。

未来 diagnostics API source mode 只能消费安全摘要，不能消费 raw payload。

## 4. base_dir 安全要求

未来 reader 的 `base_dir` 只能来自明确配置项，例如：

```text
MT4_DEMO_READONLY_BRIDGE_DIR
```

当前工单不读取 `.env`，不实现配置读取，不实现 reader。

未来必须规定：

- `base_dir` 必须显式配置。
- `base_dir` 为空则 blocked。
- `base_dir` 不是 string 则 blocked。
- `base_dir` 不能指向项目 `data/` 运行目录。
- `base_dir` 不能指向 `.env` 所在目录。
- `base_dir` 不能指向 logs / database / cache 目录。
- `base_dir` 不能由用户前端输入直接传入。
- `base_dir` 不能来自 API request body。
- `base_dir` 不能被 Dashboard 改写。
- `base_dir` 不能被 Agent / LLM 改写。
- `base_dir` 不能允许路径穿越。
- `base_dir` 不能用作目录搜索起点。

未来 reader 的 base_dir 校验失败时必须 fail closed，不得尝试 fallback 到当前工作目录、用户主目录、项目根目录或任意默认路径。

## 5. 读取行为安全要求

未来 reader 可以做：

- 对三个白名单文件执行只读 JSON 加载。
- 解析 JSON object。
- 调用 schema validators。
- 调用 source summary adapter。
- 返回安全 summary。

未来 reader 不可以做：

- 写文件。
- 修改文件。
- 删除文件。
- 创建文件。
- 扫描目录。
- 递归查找。
- glob 任意文件。
- 读取非白名单文件。
- 读取 raw payload 给 UI。
- 返回完整 payload。
- 返回敏感字段值。
- 返回 `ticket` / `order_id`。
- 返回 `suggested_lot` / `final_lot`。
- 返回 `buy` / `sell` / `open` / `close`。
- 调用 EA。
- 调用 MT4。
- 调用网络。
- 调用交易执行模块。
- 调用 RiskGate。
- 调用 PositionSizing。
- 调用 ExecutionGate。
- 生成 TradePlan。

未来 reader 即使成功读取三个文件，也只能说明 demo readonly source summary 可用于内部只读诊断，不代表可以交易，不代表可以执行，不代表可以接入自动化。

## 6. 失败策略

未来 reader 必须覆盖以下失败场景：

- `base_dir` missing。
- `base_dir` invalid。
- filename whitelist failed。
- file missing。
- file unreadable。
- invalid JSON。
- JSON not object。
- schema validation failed。
- forbidden field detected。
- source summary blocked。
- stale data。
- partial data。
- unexpected component。
- unsafe path。
- exception during read。

每种失败都必须：

- `passed=false`。
- safety blocked。
- 不泄漏 raw path。
- 不泄漏 raw payload。
- 不泄漏 exception 原文。
- 不泄漏 traceback。
- 不泄漏 Windows 用户路径。
- 不泄漏 Python 文件路径。
- 不泄漏账号、密码、token、secret。
- 保持 `read_only=true`。
- 保持 `demo_only=true`。
- 保持 `can_execute=false`。
- 保持 `is_tradable=false`。
- 保持 `is_trading_permission=false`。
- 保持 `is_execution_instruction=false`。
- 保持 `allowed_to_call_ea=false`。
- 保持 `allowed_to_modify_risk=false`。

失败响应允许包含安全 reason code，例如：

- `base_dir_missing`
- `base_dir_invalid`
- `filename_whitelist_failed`
- `file_missing`
- `file_unreadable`
- `invalid_json`
- `json_not_object`
- `schema_validation_failed`
- `forbidden_field_detected`
- `source_summary_blocked`
- `stale_data`
- `partial_data`
- `unexpected_component`
- `unsafe_path`
- `reader_exception_sanitized`

失败响应不得包含原始文件路径、异常消息、traceback、raw payload、敏感字段值、交易字段值或执行字段值。

## 7. 与 API 的关系

当前工单不接 API。

未来 API source mode 接入必须另开工单。未来 API 集成必须遵守：

- diagnostics API 只能消费安全 summary。
- explanation API 只能消费安全 summary。
- Dashboard 只能展示 mapper 后的安全字段。
- API 不能返回 raw payload。
- API 不能返回 candidate_path。
- API 不能返回 system path。
- API 不能返回 forbidden values。
- API 不能返回交易建议。
- API 不能返回执行指令。
- API 不能返回 EA 命令。
- API 不能返回 `suggested_lot` / `final_lot`。
- API 不能返回 `buy` / `sell` / `open` / `close` 指令。

未来 diagnostics API 若支持 `mt4_demo_readonly_file_bridge_enabled` source mode，必须只消费 reader 产生的 `DemoReadOnlySourceSummary`，不能直接消费文件 payload。

## 8. 与 MT4 / EA / MQL4 的关系

未来 reader 与 MT4 / EA / MQL4 的关系必须保持只读边界：

- reader 不连接 MT4 terminal。
- reader 不调用 EA。
- reader 不写 MQL4。
- reader 不发送命令。
- reader 不调用 `OrderSend`。
- reader 不调用 `OrderClose`。
- reader 不调用 `OrderModify`。
- reader 不调用 `OrderDelete`。
- 文件桥接只是未来由 MT4 侧产生只读 JSON 文件。
- Python 后端只读这些文件。
- 即使读取成功，也不代表可以交易。
- 即使三个文件全部 valid，也不代表可以执行。
- 即使 source summary ready，也不代表风控放行、仓位计算放行或自动交易放行。

任何 MT4、EA、MQL4、交易执行或账号连接能力都必须另开阶段，并通过新的契约、测试和人工验收。

## 9. Safety Flags

未来 reader 和 summary 输出必须始终保持：

- `read_only=true`
- `demo_only=true`
- `is_tradable=false`
- `can_execute=false`
- `is_trading_permission=false`
- `is_execution_instruction=false`
- `allowed_to_call_ea=false`
- `allowed_to_modify_risk=false`

这些字段不能被 API、Dashboard、Agent、LLM、配置项、用户输入或任何运行时状态改写成交易许可、执行许可、风控放行、仓位计算许可或 EA 调用许可。

## 10. 未来 Reader 测试规划

未来 reader 测试必须至少覆盖：

- valid three files produce safe summary。
- missing file blocked。
- unreadable file blocked。
- invalid JSON blocked。
- JSON array blocked。
- forbidden field blocked。
- unknown field blocked。
- unsafe filename blocked。
- unsafe base_dir blocked。
- reader does not scan directory。
- reader does not glob arbitrary files。
- reader does not write files。
- reader does not access network。
- reader does not connect MT4。
- reader does not expose raw payload。
- reader does not expose system path。
- reader does not expose exception text。
- reader does not expose password / token / secret / login / account_number。
- reader does not expose ticket / order_id。
- reader does not return trading fields。
- reader does not return execution fields。
- safety flags always safe。

建议测试使用 pytest 临时目录和 monkeypatch：

- monkeypatch `open` / `Path.read_text` 时只允许未来 reader 的受控读取路径。
- monkeypatch `glob.glob`、`os.walk`、`Path.iterdir`，如果被调用则失败。
- monkeypatch network client，如果被调用则失败。
- monkeypatch MT4 / EA / execution symbols，如果被调用则失败。
- 构造异常时必须确认异常原文、traceback、Windows 用户路径和 Python 文件路径不出现在 summary 中。

测试不得依赖真实 MT4 文件，不得读取真实 `data/` 运行目录，不得读取 `.env`，不得读写用户文件系统。

## 11. 当前仍不实现

当前 1V-1 工单仍不实现：

- reader。
- env/config loader。
- API source_mode。
- diagnostics API 接入。
- explanation API 接入。
- Dashboard 接入。
- MT4 接入。
- EA / MQL4。
- 账号连接。
- 交易执行链路。
- RiskGate。
- PositionSizing。
- ExecutionGate。
- TradePlanSchema。
- 自动交易。
- 真实交易建议。

本文档只是未来 reader 的 integration contract。下一步若进入实现阶段，必须另开工单，并继续保持 demo-only、read-only、non-trading、non-execution 的安全边界。
