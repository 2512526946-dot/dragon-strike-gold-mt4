type ExplanationWarningListProps = {
  warnings: string[];
  warningReasons: string[];
};

export function ExplanationWarningList({
  warnings,
  warningReasons,
}: ExplanationWarningListProps) {
  const items = [...warnings, ...warningReasons];

  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-warnings-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Warning Explanations</p>
        <h3 id="demo-explanation-warnings-title">只读警告说明</h3>
      </div>
      {items.length > 0 ? (
        <ul className="demo-diagnostics-readiness-grid">
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <div className="demo-diagnostics-empty-state">
          <strong>暂无警告说明</strong>
          <p>当前没有可展示的只读警告原因。</p>
        </div>
      )}
      <div className="demo-diagnostics-safety-copy">
        <p>警告只解释诊断、展示或流程状态，不构成交易动作。</p>
      </div>
    </section>
  );
}
