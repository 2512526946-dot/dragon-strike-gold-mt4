const systemStatusItems = [
  "当前阶段：Frontend Interaction Preview",
  "数据源：Mock",
  "信号类型：Placeholder",
  "MT4：未连接",
  "真实行情：未启用",
  "自动交易：禁用",
  "真实交易建议：禁用",
];

export function SystemStatusBar() {
  return (
    <section className="system-status-bar" aria-label="系统状态栏">
      <div className="system-status-heading">
        <span>系统状态栏</span>
        <strong>开发预览</strong>
      </div>
      <ul className="system-status-list">
        {systemStatusItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
