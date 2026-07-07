import type { DemoReadOnlyExplanationViewModel } from "../types";

type ExplanationStatusPanelProps = {
  viewModel: DemoReadOnlyExplanationViewModel;
};

export function ExplanationStatusPanel({ viewModel }: ExplanationStatusPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-status-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Status Metadata</p>
        <h3 id="demo-explanation-status-title">解释报告状态</h3>
      </div>
      <dl className="demo-diagnostics-summary-grid">
        <div>
          <dt>statusCode</dt>
          <dd>{viewModel.statusCode}</dd>
        </div>
        <div>
          <dt>reportType</dt>
          <dd>{viewModel.reportType}</dd>
        </div>
        <div>
          <dt>reportVersion</dt>
          <dd>{viewModel.reportVersion}</dd>
        </div>
        <div>
          <dt>generatedAt</dt>
          <dd>{viewModel.generatedAt ?? "unknown"}</dd>
        </div>
        <div>
          <dt>sourceScope</dt>
          <dd>{viewModel.sourceScope}</dd>
        </div>
        <div>
          <dt>explanationScope</dt>
          <dd>{viewModel.explanationScope}</dd>
        </div>
        <div>
          <dt>inputStatusCode</dt>
          <dd>{viewModel.inputStatusCode}</dd>
        </div>
        <div>
          <dt>inputPassed</dt>
          <dd>{viewModel.inputPassed ? "是" : "否"}</dd>
        </div>
      </dl>
      <div className="demo-diagnostics-safety-copy">
        <p>passed=true 只代表解释报告可安全展示，不代表交易许可。</p>
      </div>
    </section>
  );
}
