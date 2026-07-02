# 巨龙出击

英文项目名：dragon-strike-gold-mt4

巨龙出击是面向新手的 TradeMax Global MT4 黄金交易稳健型买卖点辅助决策系统。第一阶段只负责分析和提示买卖观察点，由使用者本人在 MT4 手动下单。

## 当前工单

工单 0B-2A：占位信号结构 + 占位信号接口。

本轮只新增开发用占位信号数据结构、PlaceholderSignalService、`GET /api/signals/placeholder` 接口和基础测试。不包含信号日志保存、真实信号生命周期、真实行情、真实 MT4 文件桥接、前端页面、交易策略、风控计算、机器学习、大模型、自动复盘、GoLiveGate 或自动交易。

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

示例配置：

```env
DEFAULT_SYMBOL=XAUUSD
DATA_SOURCE=mock
MOCK_INITIAL_PRICE=2030.00
MOCK_SPREAD=0.30
MOCK_DIGITS=2
```

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

- 信号日志保存
- MT4 文件桥接
- 前端看板
- 真实行情
- 10x 风控
- 不隔夜规则
- 亚洲时间过滤
- 真实信号生命周期
- 自动复盘
- GoLiveGate
- 机器学习
- 大模型复盘
- 自动交易，且自动交易第一阶段禁止
