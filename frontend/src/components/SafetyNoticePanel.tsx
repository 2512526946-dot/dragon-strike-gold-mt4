const safetyNoticeItems = [
  "当前系统仅为开发预览",
  "当前数据为 Mock / Placeholder",
  "不是真实交易建议",
  "不会自动下单",
  "不会连接真实账户",
  "不会连接 MT4 实盘",
  "不能作为真实交易依据",
];

export function SafetyNoticePanel() {
  return (
    <section className="safety-notice-panel" aria-labelledby="safety-notice-title">
      <div className="safety-notice-heading">
        <p>Safety Notice</p>
        <h2 id="safety-notice-title">开发预览安全提示</h2>
      </div>
      <ul className="safety-notice-list">
        {safetyNoticeItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
