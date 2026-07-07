type ExplanationForbiddenActionsPanelProps = {
  actions: string[];
};

export function ExplanationForbiddenActionsPanel({
  actions,
}: ExplanationForbiddenActionsPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-forbidden-actions-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Stage Limits</p>
        <h3 id="demo-explanation-forbidden-actions-title">
          当前不可用能力与阶段限制
        </h3>
      </div>
      {actions.length > 0 ? (
        <ul className="demo-diagnostics-readiness-grid">
          {actions.map((action, index) => (
            <li key={`${action}-${index}`}>{action}</li>
          ))}
        </ul>
      ) : (
        <div className="demo-diagnostics-empty-state">
          <strong>暂无阶段限制说明</strong>
          <p>当前没有额外的不可用能力说明。</p>
        </div>
      )}
      <div className="demo-diagnostics-safety-copy">
        <p>这些内容只作为限制说明展示，不会变成行动建议。</p>
      </div>
    </section>
  );
}
