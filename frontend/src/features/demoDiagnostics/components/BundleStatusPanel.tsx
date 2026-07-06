import type { BundleStatusViewModel } from "../types";

type BundleStatusPanelProps = {
  bundle: BundleStatusViewModel;
};

export function BundleStatusPanel({ bundle }: BundleStatusPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-diagnostics-bundle-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Bundle Status</p>
        <h3 id="demo-diagnostics-bundle-title">Bundle 校验摘要</h3>
      </div>
      <dl className="demo-diagnostics-summary-grid">
        <div>
          <dt>passed</dt>
          <dd>{bundle.passed ? "通过" : "阻断"}</dd>
        </div>
        <div>
          <dt>status</dt>
          <dd>{bundle.status}</dd>
        </div>
        <div>
          <dt>status_code</dt>
          <dd>{bundle.status_code}</dd>
        </div>
      </dl>
      <div className="demo-diagnostics-reason-grid">
        <div>
          <strong>bundle block summary</strong>
          <p>{bundle.block_summary}</p>
        </div>
        <div>
          <strong>bundle warning summary</strong>
          <p>{bundle.warning_summary}</p>
        </div>
      </div>
    </section>
  );
}
