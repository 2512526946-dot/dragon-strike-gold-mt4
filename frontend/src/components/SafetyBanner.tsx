const safetyItems = [
  { label: "自动交易", value: "禁用" },
  { label: "真实交易建议", value: "禁用" },
  { label: "MT4 实盘连接", value: "未启用" },
  { label: "当前页面", value: "静态预览" },
];

export function SafetyBanner() {
  return (
    <section className="safety-band" aria-label="安全状态">
      {safetyItems.map((item) => (
        <div className="safety-item" key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </section>
  );
}
