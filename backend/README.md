# 巨龙出击 Backend

FastAPI 后端基础项目，当前仅包含健康检查、配置读取和日志初始化。

## 启动

```powershell
cd dragon-strike-gold-mt4\backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 测试

```powershell
pytest
```

## 当前范围

工单 0A 只提供 `/health` 接口和基础工程骨架，不包含行情、策略、前端、机器学习、大模型、复盘或自动交易功能。
