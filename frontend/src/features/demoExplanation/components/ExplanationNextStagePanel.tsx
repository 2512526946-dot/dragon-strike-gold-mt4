type ExplanationNextStagePanelProps = {
  nextAllowedStageExplanation: string[];
  nextBlockedStageExplanation: string[];
};

export function ExplanationNextStagePanel({
  nextAllowedStageExplanation,
  nextBlockedStageExplanation,
}: ExplanationNextStagePanelProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-next-stage-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Next Stage Explanation</p>
        <h3 id="demo-explanation-next-stage-title">阶段流程提示</h3>
      </div>
      <div className="demo-diagnostics-readiness-grid">
        <div>
          <strong>nextAllowedStageExplanation</strong>
          <ul>
            {nextAllowedStageExplanation.length > 0 ? (
              nextAllowedStageExplanation.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))
            ) : (
              <li>暂无下一阶段流程提示。</li>
            )}
          </ul>
        </div>
        <div>
          <strong>nextBlockedStageExplanation</strong>
          <ul>
            {nextBlockedStageExplanation.length > 0 ? (
              nextBlockedStageExplanation.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))
            ) : (
              <li>暂无下一阶段阻断提示。</li>
            )}
          </ul>
        </div>
      </div>
      <div className="demo-diagnostics-safety-copy">
        <p>next_allowed_stage 只是流程提示，不是交易许可。</p>
      </div>
    </section>
  );
}
