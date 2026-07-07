import type { DemoReadOnlyExplanationViewModel } from "../types";

type ExplanationSafetyBannerProps = {
  viewModel: DemoReadOnlyExplanationViewModel;
};

function yesNo(value: boolean): string {
  return value ? "是" : "否";
}

export function ExplanationSafetyBanner({
  viewModel,
}: ExplanationSafetyBannerProps) {
  const safetyBadges = [
    { label: "readOnly", value: yesNo(viewModel.readOnly) },
    { label: "demoOnly", value: yesNo(viewModel.demoOnly) },
    { label: "isTradable", value: String(viewModel.isTradable) },
    { label: "canExecute", value: String(viewModel.canExecute) },
    {
      label: "isTradingPermission",
      value: String(viewModel.isTradingPermission),
    },
    {
      label: "isExecutionInstruction",
      value: String(viewModel.isExecutionInstruction),
    },
    { label: "allowedToCallEa", value: String(viewModel.allowedToCallEa) },
    {
      label: "allowedToModifyRisk",
      value: String(viewModel.allowedToModifyRisk),
    },
  ];

  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-safety-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Explanation Safety Banner</p>
        <h3 id="demo-explanation-safety-title">只读解释安全边界</h3>
      </div>
      <ul className="demo-diagnostics-badge-list" aria-label="解释安全字段">
        {safetyBadges.map((badge) => (
          <li key={badge.label}>
            <span>{badge.label}</span>
            <strong>{badge.value}</strong>
          </li>
        ))}
      </ul>
      <div className="demo-diagnostics-safety-copy">
        <p>只读解释；非交易许可；非执行指令。</p>
        <p>交易能力禁用；执行能力禁用；demo-only；read-only。</p>
        <p>当前区块不提供交易、执行、风控修改或仓位计算能力。</p>
      </div>
    </section>
  );
}
