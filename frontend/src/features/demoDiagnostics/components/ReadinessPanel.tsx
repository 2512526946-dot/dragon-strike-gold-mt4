import type { ReadinessViewModel } from "../types";

type ReadinessPanelProps = {
  readiness: ReadinessViewModel;
};

function renderItems(values: string[], emptyText: string) {
  if (values.length === 0) {
    return <p>{emptyText}</p>;
  }

  return (
    <ul>
      {values.map((value) => (
        <li key={value}>{value}</li>
      ))}
    </ul>
  );
}

export function ReadinessPanel({ readiness }: ReadinessPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-diagnostics-readiness-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Readiness Panel</p>
        <h3 id="demo-diagnostics-readiness-title">阶段可读性提示</h3>
      </div>
      <div className="demo-diagnostics-readiness-grid">
        <div>
          <strong>readiness_notes</strong>
          {renderItems(readiness.readiness_notes, "暂无只读提示。")}
        </div>
        <div>
          <strong>next_allowed_stage</strong>
          {renderItems(readiness.next_allowed_stage, "暂无下一规划阶段。")}
          <p>next_allowed_stage 是流程提示，不是交易许可。</p>
        </div>
        <div>
          <strong>next_blocked_stage</strong>
          {renderItems(readiness.next_blocked_stage, "暂无阶段限制摘要。")}
          <p>next_blocked_stage 是阶段限制，不是交易指令。</p>
        </div>
      </div>
    </section>
  );
}
