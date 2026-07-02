import { ConstraintPanel } from "./components/ConstraintPanel";
import { SafetyBanner } from "./components/SafetyBanner";
import { StatusCard } from "./components/StatusCard";

const statusCards = [
  { label: "数据状态", value: "Mock 模式" },
  { label: "行情接口", value: "后续接入" },
  { label: "占位信号", value: "后续接入" },
  { label: "信号日志", value: "后续接入" },
  { label: "GoLiveGate", value: "未启用" },
];

function App() {
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
