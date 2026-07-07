type ExplanationBlockerListProps = {
  blockers: string[];
  blockReasons: string[];
};

export function ExplanationBlockerList({
  blockers,
  blockReasons,
}: ExplanationBlockerListProps) {
  const items = [...blockers, ...blockReasons];

  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-blockers-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Blocker Explanations</p>
        <h3 id="demo-explanation-blockers-title">只读阻断说明</h3>
      </div>
      {items.length > 0 ? (
        <ul className="demo-diagnostics-readiness-grid">
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <div className="demo-diagnostics-empty-state">
          <strong>暂无阻断说明</strong>
          <p>当前没有可展示的只读阻断原因。</p>
        </div>
      )}
      <div className="demo-diagnostics-safety-copy">
        <p>阻断只解释诊断、流程或展示限制，不提供交易动作。</p>
      </div>
    </section>
  );
}
