# 巨龙出击 Frontend

前端当前为 0C-2A 首页预览，只展示项目阶段、安全状态、交易约束说明和后端 `/health` 连接状态。

本轮只请求后端 `/health` 接口，不请求行情接口，不请求信号接口，不接入实时行情，不展示图表，不返回真实交易建议。

## 后端地址配置

前端通过 Vite 环境变量读取后端地址：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8000
```

如果未配置，默认使用 `http://127.0.0.1:8000`。本地可参考 `frontend/.env.example`，不要提交 `frontend/.env`。

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
