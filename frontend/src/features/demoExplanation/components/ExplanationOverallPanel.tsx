import type { DemoReadOnlyExplanationViewModel } from "../types";

type ExplanationOverallPanelProps = {
  viewModel: DemoReadOnlyExplanationViewModel;
};

export function ExplanationOverallPanel({
  viewModel,
}: ExplanationOverallPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-overall-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Overall Explanation</p>
        <h3 id="demo-explanation-overall-title">整体只读解释</h3>
      </div>
      <dl className="demo-diagnostics-summary-grid">
        <div>
          <dt>display status</dt>
          <dd>{viewModel.passed ? "可展示" : "阻断"}</dd>
        </div>
        <div>
          <dt>uiSafetyStatus</dt>
          <dd>{viewModel.uiSafetyStatus}</dd>
        </div>
      </dl>
      <div className="demo-diagnostics-safety-copy">
        <p>{viewModel.overallExplanation || "暂无整体只读解释。"}</p>
        <p>{viewModel.statusExplanation || "暂无状态解释。"}</p>
        <p>{viewModel.uiSafetyMessage}</p>
      </div>
    </section>
  );
}
