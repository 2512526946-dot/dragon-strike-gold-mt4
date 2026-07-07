import type { DemoReadOnlyExplanationViewModel } from "../types";
import { ExplanationBlockerList } from "./ExplanationBlockerList";
import { ExplanationComponentList } from "./ExplanationComponentList";
import { ExplanationForbiddenActionsPanel } from "./ExplanationForbiddenActionsPanel";
import { ExplanationNextStagePanel } from "./ExplanationNextStagePanel";
import { ExplanationOverallPanel } from "./ExplanationOverallPanel";
import { ExplanationReadinessPanel } from "./ExplanationReadinessPanel";
import { ExplanationSafeNextStepsPanel } from "./ExplanationSafeNextStepsPanel";
import { ExplanationSafetyBanner } from "./ExplanationSafetyBanner";
import { ExplanationStatusPanel } from "./ExplanationStatusPanel";
import { ExplanationWarningList } from "./ExplanationWarningList";

export type DemoReadOnlyExplanationPanelProps = {
  viewModel: DemoReadOnlyExplanationViewModel;
};

function stateTitle(uiSafetyStatus: DemoReadOnlyExplanationViewModel["uiSafetyStatus"]) {
  switch (uiSafetyStatus) {
    case "ready":
      return "只读解释可展示";
    case "blocked":
      return "只读解释被阻断";
    case "api_error":
      return "只读解释读取失败";
    case "security_blocked":
      return "SECURITY BLOCKED";
    case "empty":
      return "暂无只读解释";
    case "stale_or_unknown":
      return "只读解释状态未知";
    default:
      return "只读解释状态未知";
  }
}

function stateDescription(
  uiSafetyStatus: DemoReadOnlyExplanationViewModel["uiSafetyStatus"],
) {
  switch (uiSafetyStatus) {
    case "ready":
      return "解释报告已经经过 ViewModel 清洗，可用于只读展示。";
    case "blocked":
      return "解释报告处于阻断状态，仅展示诊断、流程或展示限制。";
    case "api_error":
      return "解释报告读取失败，本组件不展示异常原文或系统路径。";
    case "security_blocked":
      return "响应触发安全阻断，本组件不展示原始内容或敏感字段。";
    case "empty":
      return "当前没有解释内容，本组件不会主动请求数据。";
    case "stale_or_unknown":
      return "当前解释状态未知，本组件不会主动刷新。";
    default:
      return "当前解释状态未知，本组件保持只读展示。";
  }
}

export function DemoReadOnlyExplanationPanel({
  viewModel,
}: DemoReadOnlyExplanationPanelProps) {
  const isSecurityBlocked = viewModel.uiSafetyStatus === "security_blocked";

  return (
    <section
      className="demo-diagnostics-dashboard"
      aria-labelledby="demo-readonly-explanation-panel-title"
    >
      <div className="demo-diagnostics-dashboard-heading">
        <div>
          <p>Demo-only Read-only Explanation</p>
          <h2 id="demo-readonly-explanation-panel-title">
            DemoReadOnlyExplanationPanel
          </h2>
          <span>
            纯只读解释区块；非交易许可；非执行指令；交易能力禁用；执行能力禁用。
          </span>
        </div>
      </div>

      <div
        className={`demo-diagnostics-empty-state${
          isSecurityBlocked ? " is-security-blocked" : ""
        }`}
      >
        <strong>{stateTitle(viewModel.uiSafetyStatus)}</strong>
        <p>{stateDescription(viewModel.uiSafetyStatus)}</p>
        <p>本组件只接收清洗后的 ViewModel，不主动请求 API，不提供交互动作。</p>
      </div>

      <div className="demo-diagnostics-panel-stack">
        <ExplanationSafetyBanner viewModel={viewModel} />
        <ExplanationOverallPanel viewModel={viewModel} />
        <ExplanationStatusPanel viewModel={viewModel} />
        <ExplanationComponentList components={viewModel.componentExplanations} />
        <ExplanationBlockerList
          blockers={viewModel.blockerExplanations}
          blockReasons={viewModel.blockReasons}
        />
        <ExplanationWarningList
          warnings={viewModel.warningExplanations}
          warningReasons={viewModel.warningReasons}
        />
        <ExplanationReadinessPanel
          readinessExplanation={viewModel.readinessExplanation}
          unknowns={viewModel.unknowns}
          notes={viewModel.notes}
        />
        <ExplanationNextStagePanel
          nextAllowedStageExplanation={viewModel.nextAllowedStageExplanation}
          nextBlockedStageExplanation={viewModel.nextBlockedStageExplanation}
        />
        <ExplanationSafeNextStepsPanel steps={viewModel.userSafeNextSteps} />
        <ExplanationForbiddenActionsPanel
          actions={viewModel.userForbiddenActions}
        />
      </div>
    </section>
  );
}
