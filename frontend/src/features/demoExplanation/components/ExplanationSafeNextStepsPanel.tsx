type ExplanationSafeNextStepsPanelProps = {
  steps: string[];
};

export function ExplanationSafeNextStepsPanel({
  steps,
}: ExplanationSafeNextStepsPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-safe-next-steps-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Safe Next Steps</p>
        <h3 id="demo-explanation-safe-next-steps-title">安全下一步</h3>
      </div>
      {steps.length > 0 ? (
        <ul className="demo-diagnostics-readiness-grid">
          {steps.map((step, index) => (
            <li key={`${step}-${index}`}>{step}</li>
          ))}
        </ul>
      ) : (
        <div className="demo-diagnostics-empty-state">
          <strong>暂无安全下一步</strong>
          <p>当前没有可展示的非交易动作提示。</p>
        </div>
      )}
      <div className="demo-diagnostics-safety-copy">
        <p>本区块不新增组件自定义交易动作，也不提供请求入口。</p>
      </div>
    </section>
  );
}
