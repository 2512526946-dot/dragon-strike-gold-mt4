const constraints = [
  ["账户货币", "USD"],
  ["主要交易品种", "XAUUSD"],
  ["主要周期", "H1"],
  ["确认周期", "M15"],
  ["是否隔夜", "不允许（不隔夜）"],
  ["单笔最大风险", "1%"],
  ["单日最大风险", "3%"],
];

export function ConstraintPanel() {
  return (
    <section className="constraint-panel" aria-labelledby="constraint-title">
      <div className="section-heading">
        <p>Trading Constraints</p>
        <h2 id="constraint-title">交易约束</h2>
      </div>
      <dl className="constraint-list">
        {constraints.map(([label, value]) => (
          <div className="constraint-row" key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
