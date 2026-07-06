import { useState } from "react";

import { getDemoReadOnlyDiagnostics } from "../api";
import { SECURITY_BLOCKED_MESSAGE } from "../contracts";
import type { DemoDiagnosticsViewModel } from "../types";
import { BundleStatusPanel } from "./BundleStatusPanel";
import { ComponentStatusList } from "./ComponentStatusList";
import { OverallStatusPanel } from "./OverallStatusPanel";
import { ReadinessPanel } from "./ReadinessPanel";

type DashboardState =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "ready"; diagnostics: DemoDiagnosticsViewModel }
  | { state: "error"; message: string };

export function DemoReadOnlyDiagnosticsDashboard() {
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    state: "idle",
  });

  async function handleRefreshDiagnostics() {
    setDashboardState({ state: "loading" });

    try {
      const diagnostics = await getDemoReadOnlyDiagnostics();
      setDashboardState({ state: "ready", diagnostics });
    } catch {
      setDashboardState({
        state: "error",
        message:
          "无法读取 Demo 只读诊断。请确认后端已启动；页面不会展示原始错误对象或系统路径。",
      });
    }
  }

  const diagnostics =
    dashboardState.state === "ready" ? dashboardState.diagnostics : null;
  const isLoading = dashboardState.state === "loading";
  const isSecurityBlocked = diagnostics?.ui_state === "security_blocked";

  return (
    <section
      className="demo-diagnostics-dashboard"
      aria-labelledby="demo-diagnostics-dashboard-title"
    >
      <div className="demo-diagnostics-dashboard-heading">
        <div>
          <p>Demo-only Read-only Diagnostics</p>
          <h2 id="demo-diagnostics-dashboard-title">
            DemoReadOnlyDiagnostics Dashboard
          </h2>
          <span>只读诊断观察层，不生成交易建议，不提供执行能力。</span>
        </div>
        <button
          type="button"
          onClick={handleRefreshDiagnostics}
          disabled={isLoading}
          aria-busy={isLoading}
        >
          {isLoading ? "正在加载只读诊断" : "刷新 Demo 只读诊断"}
        </button>
      </div>

      {dashboardState.state === "idle" ? (
        <div className="demo-diagnostics-empty-state">
          <strong>尚未读取 Demo 只读诊断</strong>
          <p>点击刷新按钮后，才会请求只读诊断 API。当前没有自动轮询。</p>
        </div>
      ) : null}

      {isLoading ? (
        <div className="demo-diagnostics-empty-state">
          <strong>正在加载只读诊断</strong>
          <p>当前只等待安全摘要，不展示任何原始响应。</p>
        </div>
      ) : null}

      {dashboardState.state === "error" ? (
        <div className="demo-diagnostics-empty-state is-error">
          <strong>只读诊断读取失败</strong>
          <p>{dashboardState.message}</p>
          <p>安全错误态不会展示调试细节、系统路径或原始错误对象。</p>
        </div>
      ) : null}

      {isSecurityBlocked ? (
        <div className="demo-diagnostics-empty-state is-security-blocked">
          <strong>{SECURITY_BLOCKED_MESSAGE}</strong>
          <p>响应包含不安全字段，或安全字段不满足只读契约。</p>
          <p>页面已阻断展示，不暴露原始响应、敏感字段、原始业务内容或本机路径细节。</p>
        </div>
      ) : null}

      {diagnostics && !isSecurityBlocked ? (
        <div className="demo-diagnostics-panel-stack">
          <OverallStatusPanel diagnostics={diagnostics} />
          <BundleStatusPanel bundle={diagnostics.bundle} />
          <ComponentStatusList components={diagnostics.components} />
          <ReadinessPanel readiness={diagnostics.readiness} />
        </div>
      ) : null}
    </section>
  );
}
