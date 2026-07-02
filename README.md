# 巨龙出击

英文项目名：dragon-strike-gold-mt4

巨龙出击是面向新手的 TradeMax Global MT4 黄金交易稳健型买卖点辅助决策系统。第一阶段只负责分析和提示买卖观察点，由使用者本人在 MT4 手动下单。

## 当前工单

工单 0C-2A：前端接入 /health，显示后端连接状态。

本轮只让前端读取后端 `GET /health`，首页显示后端在线/离线状态和健康检查字段。前端不请求行情接口，不请求信号接口，不展示实时行情或图表，不包含真实信号或交易建议。

## 启动后端

```powershell
cd dragon-strike-gold-mt4\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

Mock 行情快照：

```powershell
curl http://127.0.0.1:8000/api/market/snapshot
```

占位信号：

```powershell
curl http://127.0.0.1:8000/api/signals/placeholder
```

保存占位信号日志：

```powershell
curl -X POST http://127.0.0.1:8000/api/signals/placeholder/log
```

## 启动前端

```powershell
cd dragon-strike-gold-mt4\frontend
npm.cmd install
npm.cmd run dev
```

构建：

```powershell
cd dragon-strike-gold-mt4\frontend
npm.cmd run build
```

前端后端地址配置：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8000
```

未配置时默认使用 `http://127.0.0.1:8000`。本地配置可参考 `frontend/.env.example`，不要提交 `frontend/.env`。

## 前端首页

首页显示：

- 项目名称：巨龙出击
- 副标题：TradeMax MT4 Gold Decision Copilot
- 当前阶段：Mock Core / Frontend Static Preview
- 系统定位：黄金 MT4 稳健型买卖点辅助决策系统
- 交易方式：系统只做辅助观察，用户手动下单
- 后端连接状态：在线时显示 `project`、`name`、`version`、`stage`，离线时提示无法连接后端，仅显示静态预览
- 安全状态：自动交易禁用、真实交易建议禁用、MT4 实盘连接未启用、当前页面为静态预览
- 交易约束：USD、XAUUSD、H1、M15、不允许隔夜、单笔最大风险 1%、单日最大风险 3%

## Mock 行情接口

`GET /api/market/snapshot` 返回 XAUUSD 的开发模拟 Bid / Ask / Spread 快照。

返回数据会明确标记：

- `source=mock`
- `is_mock=true`
- `is_tradable=false`
- `note=Mock market data for development only. Not a trading signal.`

该接口仅用于后端开发和接口测试，不是交易信号，不可用于真实交易。

## 占位信号接口

`GET /api/signals/placeholder` 返回开发用占位信号。

返回数据会明确标记：

- `source=placeholder`
- `action=observe_only`
- `signal_type=placeholder_only`
- `final_score=0`
- `allow_chasing=false`
- `suggested_lot=0`
- `is_placeholder=true`
- `is_tradable=false`
- `note=Placeholder signal for development only. Not a trading recommendation.`

该接口只用于后端接口联调和后续结构验证，不是交易建议，不能用于真实下单。

## 占位信号日志接口

`POST /api/signals/placeholder/log` 会生成一个开发用占位信号，并把日志写入 JSONL 文件。

默认日志路径：

```text
data/signals/placeholder_signals.jsonl
```

日志数据会明确标记：

- `log_type=placeholder_signal`
- `source=placeholder`
- `action=observe_only`
- `final_score=0`
- `suggested_lot=0`
- `allow_chasing=false`
- `is_placeholder=true`
- `is_tradable=false`
- `note=Placeholder signal log for development only. Not a trading recommendation.`

该日志仅用于开发验证，不是交易建议，不能用于真实下单。运行生成的 JSONL 文件位于 `data/signals/`，该目录下运行数据已被 `.gitignore` 忽略。

## 运行测试

```powershell
cd dragon-strike-gold-mt4\backend
python -m pytest
```

## 安全红线

第一阶段严禁自动交易。系统只提供分析和观察提示，不负责下单、平仓、改止损或连接真实账户执行交易。

禁止事项：

- OrderSend
- OrderClose
- OrderModify
- OrderDelete
- 自动下单逻辑
- 自动平仓逻辑
- 自动改止损逻辑
- 马丁格尔
- 网格加仓
- 真实账户自动交易

## 当前未实现功能

- 前端请求行情接口
- 前端请求信号接口
- 实时行情
- 图表
- 真实信号生命周期
- MT4 文件桥接
- 真实行情
- 10x 风控
- 不隔夜规则真实逻辑
- 亚洲时间过滤真实逻辑
- 自动复盘
- GoLiveGate
- 机器学习
- 大模型复盘
- 自动交易，且自动交易第一阶段禁止
