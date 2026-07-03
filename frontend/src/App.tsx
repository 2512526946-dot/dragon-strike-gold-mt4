import { useEffect, useState } from "react";

import { fetchHealth, type HealthResponse } from "./api/health";
import { fetchMarketSnapshot, type MarketSnapshot } from "./api/market";
import { BackendStatusCard } from "./components/BackendStatusCard";
import { ConstraintPanel } from "./components/ConstraintPanel";
import { MarketSnapshotCard } from "./components/MarketSnapshotCard";
import { SafetyBanner } from "./components/SafetyBanner";
import { StatusCard } from "./components/StatusCard";

type BackendStatus =
  | { state: "loading" }
  | { state: "online"; health: HealthResponse }
  | { state: "offline"; message: string };

type MarketSnapshotStatus =
  | { state: "loading" }
  | { state: "ready"; snapshot: MarketSnapshot }
  | { state: "error"; message: string };

const statusCards = [
  { label: "数据状态", value: "Mock 模式" },
  { label: "行情接口", value: "Mock 已接入" },
  { label: "占位信号", value: "后续接入" },
  { label: "信号日志", value: "后续接入" },
  { label: "GoLiveGate", value: "未启用" },
];

function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    state: "loading",
  });
  const [marketStatus, setMarketStatus] = useState<MarketSnapshotStatus>({
    state: "loading",
  });

  function loadMarketSnapshot() {
    setMarketStatus({ state: "loading" });

    fetchMarketSnapshot()
      .then((snapshot) => {
        setMarketStatus({ state: "ready", snapshot });
      })
      .catch(() => {
        setMarketStatus({
          state: "error",
          message: "无法获取 Mock 行情，仅显示静态预览",
        });
      });
  }

  useEffect(() => {
    let isMounted = true;

    fetchHealth()
      .then((health) => {
        if (isMounted) {
          setBackendStatus({ state: "online", health });
        }
      })
      .catch(() => {
        if (isMounted) {
          setBackendStatus({
            state: "offline",
            message: "无法连接后端，仅显示静态预览",
          });
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    loadMarketSnapshot();
  }, []);

  return (
    <main className="app-shell">
      <section className="workspace-header" aria-labelledby="page-title">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            DS
          </div>
          <div>
            <p className="stage-label">当前阶段：Mock Core / Frontend Static Preview</p>
            <h1 id="page-title">巨龙出击</h1>
            <p className="subtitle">TradeMax MT4 Gold Decision Copilot</p>
          </div>
        </div>
        <div className="system-position">
          <span>系统定位：黄金 MT4 稳健型买卖点辅助决策系统</span>
          <strong>交易方式：系统只做辅助观察，用户手动下单</strong>
        </div>
      </section>

      <SafetyBanner />

      <BackendStatusCard status={backendStatus} />

      <MarketSnapshotCard
        status={marketStatus}
        onRefresh={loadMarketSnapshot}
      />

      <section className="dashboard-grid" aria-label="静态状态总览">
        {statusCards.map((card) => (
          <StatusCard key={card.label} label={card.label} value={card.value} />
        ))}
      </section>

      <ConstraintPanel />

      <footer className="footer-note">
        当前页面仅为开发阶段静态预览，不包含真实行情、真实信号或交易建议。
      </footer>
    </main>
  );
}

export default App;
