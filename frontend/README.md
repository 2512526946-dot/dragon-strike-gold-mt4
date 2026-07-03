# 巨龙出击 Frontend

前端当前为 0C-2B 首页预览，只展示项目阶段、安全状态、交易约束说明、后端 `/health` 连接状态和 Mock 行情快照。

本轮只请求后端 `/health` 和 `/api/market/snapshot` 接口，不请求信号接口，不自动轮询，不接入实时行情，不展示图表，不返回真实交易建议。

## 后端地址配置

前端通过 Vite 环境变量读取后端地址：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8000
```

如果未配置，默认使用 `http://127.0.0.1:8000`。本地可参考 `frontend/.env.example`，不要提交 `frontend/.env`。

## 当前接口边界

- `GET /health`：显示后端在线/离线状态。
- `GET /api/market/snapshot`：显示开发用 Mock 黄金行情快照。
- 不调用 `/api/signals/placeholder`。
- 不调用 `/api/signals/placeholder/log`。
- 不使用 WebSocket 或自动轮询。

Mock 行情卡片会明确显示：当前为开发模拟行情，不是真实行情，不是交易信号，不可用于下单。

## 启动

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

## 构建

```powershell
cd frontend
npm.cmd run build
```
