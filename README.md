# 巨龙出击

英文项目名：dragon-strike-gold-mt4

巨龙出击是面向新手的 TradeMax Global MT4 黄金交易稳健型买卖点辅助决策系统。第一阶段只负责分析和提示买卖观察点，由使用者本人在 MT4 手动下单。

## 当前工单

工单 0A：项目骨架 + 后端健康检查。

本轮只创建项目骨架、FastAPI 后端基础项目、配置读取、日志配置、`/health` 接口和基础测试。

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

## 运行测试

```powershell
cd dragon-strike-gold-mt4\backend
pytest
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

- Mock 行情
- MT4 文件桥接
- 前端看板
- 10x 风控
- 不隔夜规则
- 亚洲时间过滤
- 信号生命周期
- 自动复盘
- GoLiveGate
- 机器学习
- 大模型复盘
- 自动交易，且自动交易第一阶段禁止
