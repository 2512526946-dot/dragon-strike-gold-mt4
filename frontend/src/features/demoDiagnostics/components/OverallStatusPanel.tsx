import type { DemoDiagnosticsViewModel } from "../types";

type OverallStatusPanelProps = {
  diagnostics: DemoDiagnosticsViewModel;
};

function yesNo(value: boolean) {
  return value ? "是" : "否";
}

export function OverallStatusPanel({
  diagnostics,
}: OverallStatusPanelProps) {
  const safetyBadges = [
    { label: "read_only", value: yesNo(diagnostics.read_only) },
    { label: "demo_only", value: yesNo(diagnostics.demo_only) },
    { label: "is_tradable", value: String(diagnostics.is_tradable) },
    { label: "can_execute", value: String(diagnostics.can_execute) },
    {
      label: "is_trading_permission",
      value: String(diagnostics.is_trading_permission),
    },
    {
      label: "is_execution_instruction",
      value: String(diagnostics.is_execution_instruction),
    },
    {
      label: "allowed_to_call_ea",
      value: String(diagnostics.allowed_to_call_ea),
    },
    {
      label: "allowed_to_modify_risk",
      value: String(diagnostics.allowed_to_modify_risk),
    },
  ];

  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-diagnostics-overall-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Overall Status</p>
        <h3 id="demo-diagnostics-overall-title">整体安全状态</h3>
      </div>
      <dl className="demo-diagnostics-summary-grid">
        <div>
          <dt>passed</dt>
          <dd>{diagnostics.passed ? "通过" : "阻断"}</dd>
        </div>
        <div>
          <dt>status_code</dt>
          <dd>{diagnostics.status_code}</dd>
        </div>
        <div>
          <dt>validation_stage</dt>
          <dd>{diagnostics.validation_stage}</dd>
        </div>
        <div>
          <dt>source_scope</dt>
          <dd>{diagnostics.source_scope}</dd>
        </div>
      </dl>
      <ul className="demo-diagnostics-badge-list" aria-label="安全字段">
        {safetyBadges.map((badge) => (
          <li key={badge.label}>
            <span>{badge.label}</span>
            <strong>{badge.value}</strong>
          </li>
        ))}
      </ul>
      <div className="demo-diagnostics-safety-copy">
        <p>只读诊断；非交易许可；非执行指令。</p>
        <p>交易能力禁用；执行能力禁用；无自动执行入口。</p>
      </div>
    </section>
  );
}
