import { useEffect, useState } from "react";

import { fetchHealth, type HealthResponse } from "./api/health";
import { fetchMarketSnapshot, type MarketSnapshot } from "./api/market";
import {
  getMt4Diagnostics,
  type Mt4DiagnosticsResponse,
} from "./api/mt4Diagnostics";
import {
  createPlaceholderSignalLog,
  fetchPlaceholderSignal,
  type PlaceholderSignal,
  type PlaceholderSignalLogResponse,
} from "./api/signals";
import { BackendStatusCard } from "./components/BackendStatusCard";
import { ConstraintPanel } from "./components/ConstraintPanel";
import { MarketSnapshotCard } from "./components/MarketSnapshotCard";
import { Mt4DiagnosticsStatusCard } from "./components/Mt4DiagnosticsStatusCard";
import { PlaceholderSignalCard } from "./components/PlaceholderSignalCard";
import { PlaceholderSignalLogButton } from "./components/PlaceholderSignalLogButton";
import { SafetyBanner } from "./components/SafetyBanner";
import { SafetyNoticePanel } from "./components/SafetyNoticePanel";
import { StatusCard } from "./components/StatusCard";
import { SystemStatusBar } from "./components/SystemStatusBar";
import { ERROR_MESSAGES, ERROR_SAFETY_NOTE } from "./constants/messages";

type BackendStatus =
  | { state: "loading" }
  | { state: "online"; health: HealthResponse }
  | { state: "offline"; message: string };

type MarketSnapshotStatus =
  | { state: "loading" }
  | { state: "ready"; snapshot: MarketSnapshot }
  | { state: "error"; message: string };

type PlaceholderSignalStatus =
  | { state: "loading" }
  | { state: "ready"; signal: PlaceholderSignal }
  | { state: "error"; message: string };

type PlaceholderLogStatus =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "success"; response: PlaceholderSignalLogResponse }
  | { state: "error"; message: string };

type Mt4DiagnosticsStatus =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "ready"; diagnostics: Mt4DiagnosticsResponse }
  | { state: "error"; message: string };

const statusCards = [
  { label: "数据状态", value: "Mock 模式" },
  { label: "行情接口", value: "Mock 已接入" },
  { label: "占位信号", value: "已接入" },
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
  const [signalStatus, setSignalStatus] = useState<PlaceholderSignalStatus>({
    state: "loading",
  });
  const [placeholderLogStatus, setPlaceholderLogStatus] =
    useState<PlaceholderLogStatus>({
      state: "idle",
    });
  const [mt4DiagnosticsStatus, setMt4DiagnosticsStatus] =
    useState<Mt4DiagnosticsStatus>({
      state: "idle",
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
          message: ERROR_MESSAGES.mockMarketUnavailable,
        });
      });
  }

  function loadPlaceholderSignal() {
    setSignalStatus({ state: "loading" });

    fetchPlaceholderSignal()
      .then((signal) => {
        setSignalStatus({ state: "ready", signal });
      })
      .catch(() => {
        setSignalStatus({
          state: "error",
          message: ERROR_MESSAGES.placeholderSignalUnavailable,
        });
      });
  }

  function handlePlaceholderSignalLog() {
    setPlaceholderLogStatus({ state: "loading" });

    createPlaceholderSignalLog()
      .then((response) => {
        setPlaceholderLogStatus({ state: "success", response });
      })
      .catch(() => {
        setPlaceholderLogStatus({
          state: "error",
          message: ERROR_MESSAGES.placeholderLogWriteFailed,
        });
      });
  }

  function handleRefreshMt4Diagnostics() {
    setMt4DiagnosticsStatus({ state: "loading" });

    getMt4Diagnostics()
      .then((diagnostics) => {
        setMt4DiagnosticsStatus({ state: "ready", diagnostics });
      })
      .catch(() => {
        setMt4DiagnosticsStatus({
          state: "error",
          message:
            "无法读取 MT4 只读诊断。请确认后端已启动；只读诊断不是交易许可，不生成交易信号。",
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
            message: ERROR_MESSAGES.backendOffline,
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

  useEffect(() => {
    loadPlaceholderSignal();
  }, []);

  return (
    <main className="app-shell">
      <SystemStatusBar />
      <SafetyNoticePanel />

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

      <section
        className="mt4-diagnostics-panel"
        aria-labelledby="mt4-diagnostics-panel-title"
      >
        <div className="mt4-diagnostics-panel-heading">
          <div>
            <p>MT4 Diagnostics</p>
            <h2 id="mt4-diagnostics-panel-title">MT4 只读诊断</h2>
          </div>
          <button
            type="button"
            onClick={handleRefreshMt4Diagnostics}
            disabled={mt4DiagnosticsStatus.state === "loading"}
            aria-busy={mt4DiagnosticsStatus.state === "loading"}
          >
            {mt4DiagnosticsStatus.state === "loading"
              ? "读取中..."
              : "刷新只读诊断"}
          </button>
        </div>
        <Mt4DiagnosticsStatusCard
          loading={mt4DiagnosticsStatus.state === "loading"}
          error={
            mt4DiagnosticsStatus.state === "error"
              ? mt4DiagnosticsStatus.message
              : null
          }
          diagnostics={
            mt4DiagnosticsStatus.state === "ready"
              ? mt4DiagnosticsStatus.diagnostics
              : null
          }
        />
      </section>

      <MarketSnapshotCard
        status={marketStatus}
        onRefresh={loadMarketSnapshot}
      />

      <PlaceholderSignalCard
        status={signalStatus}
        onRefresh={loadPlaceholderSignal}
      />

      <section
        className="placeholder-log-panel"
        aria-labelledby="placeholder-log-title"
      >
        <div className="placeholder-log-heading">
          <div>
            <p>Placeholder Signal Log</p>
            <h2 id="placeholder-log-title">占位信号日志</h2>
          </div>
          <span>暂未启用</span>
        </div>
        <PlaceholderSignalLogButton
          loading={placeholderLogStatus.state === "loading"}
          label="记录占位信号"
          onClick={handlePlaceholderSignalLog}
          helperText={
            "手动点击后仅记录开发阶段占位信号日志，不是交易操作，不会下单，不会连接真实账户。"
          }
        />
        {placeholderLogStatus.state === "success" ? (
          <div className="placeholder-log-status is-success">
            <p>占位信号日志已记录。仅为开发日志，不是交易操作。</p>
            <dl className="placeholder-log-result">
              <div>
                <dt>logged</dt>
                <dd>{String(placeholderLogStatus.response.logged)}</dd>
              </div>
              <div>
                <dt>log_type</dt>
                <dd>{placeholderLogStatus.response.log_type}</dd>
              </div>
              <div>
                <dt>is_placeholder</dt>
                <dd>{String(placeholderLogStatus.response.is_placeholder)}</dd>
              </div>
              <div>
                <dt>is_tradable</dt>
                <dd>{String(placeholderLogStatus.response.is_tradable)}</dd>
              </div>
            </dl>
          </div>
        ) : null}
        {placeholderLogStatus.state === "error" ? (
          <div className="placeholder-log-status is-error">
            <p>{placeholderLogStatus.message}</p>
            <p>{ERROR_SAFETY_NOTE}</p>
          </div>
        ) : null}
      </section>

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
