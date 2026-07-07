type ExplanationReadinessPanelProps = {
  readinessExplanation: string[];
  unknowns: string[];
  notes: string[];
};

export function ExplanationReadinessPanel({
  readinessExplanation,
  unknowns,
  notes,
}: ExplanationReadinessPanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-readiness-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Readiness Explanation</p>
        <h3 id="demo-explanation-readiness-title">解释链路状态</h3>
      </div>
      <div className="demo-diagnostics-readiness-grid">
        <div>
          <strong>readiness</strong>
          <ul>
            {readinessExplanation.length > 0 ? (
              readinessExplanation.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))
            ) : (
              <li>暂无只读链路状态说明。</li>
            )}
          </ul>
        </div>
        <div>
          <strong>unknowns</strong>
          <ul>
            {unknowns.length > 0 ? (
              unknowns.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))
            ) : (
              <li>暂无未知项。</li>
            )}
          </ul>
        </div>
        <div>
          <strong>notes</strong>
          <ul>
            {notes.length > 0 ? (
              notes.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))
            ) : (
              <li>暂无备注。</li>
            )}
          </ul>
        </div>
      </div>
      <div className="demo-diagnostics-safety-copy">
        <p>readiness 只表示只读解释链路状态，不表示交易就绪。</p>
      </div>
    </section>
  );
}
