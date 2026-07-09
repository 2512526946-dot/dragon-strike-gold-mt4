import type { SourceReadinessUiModel } from "./sourceReadinessMapper";

type SourceReadinessCardProps = {
  sourceReadiness: SourceReadinessUiModel;
};

function renderItems(items: string[] | undefined, emptyText: string) {
  const safeItems = items ?? [];
  if (safeItems.length === 0) {
    return <p>{emptyText}</p>;
  }

  return (
    <ul className="source-readiness-list">
      {safeItems.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function SourceReadinessCard({
  sourceReadiness,
}: SourceReadinessCardProps) {
  const isDocsFixture =
    sourceReadiness.displaySourceModeLabel === "文档示例 / 安全 fixture";

  if (sourceReadiness.isUnsafeResponse) {
    return (
      <section
        className="source-readiness-card is-unsafe"
        aria-labelledby="source-readiness-card-title"
      >
        <div className="source-readiness-heading">
          <p>Source Readiness</p>
          <h3 id="source-readiness-card-title">响应安全检查失败</h3>
        </div>
        <p>已阻断展示危险字段。</p>
        <p>模式：只读安全阻断。</p>
        {renderItems(sourceReadiness.unsafeReasons, "已安全阻断。")}
      </section>
    );
  }

  return (
    <section
      className="source-readiness-card"
      aria-labelledby="source-readiness-card-title"
    >
      <div className="source-readiness-heading">
        <p>Source Readiness</p>
        <h3 id="source-readiness-card-title">数据源只读状态</h3>
      </div>

      <dl className="source-readiness-grid">
        <div>
          <dt>当前数据源</dt>
          <dd>{sourceReadiness.displaySourceModeLabel}</dd>
        </div>
        <div>
          <dt>数据源状态</dt>
          <dd>{sourceReadiness.displaySourceStatusLabel}</dd>
        </div>
        <div>
          <dt>配置检查</dt>
          <dd>{sourceReadiness.displaySourceConfigLabel}</dd>
        </div>
        <div>
          <dt>Reader</dt>
          <dd>{sourceReadiness.displayReaderStatusLabel}</dd>
        </div>
        <div>
          <dt>Reader 结果</dt>
          <dd>{sourceReadiness.displayReaderResultLabel}</dd>
        </div>
        <div>
          <dt>MT4 Demo 文件桥</dt>
          <dd>{sourceReadiness.displayBridgeEnabledLabel}</dd>
        </div>
        <div>
          <dt>Readiness</dt>
          <dd>{sourceReadiness.readinessBadge}</dd>
        </div>
        <div>
          <dt>模式</dt>
          <dd>
            {sourceReadiness.showAsReadOnly && sourceReadiness.showAsDemoOnly
              ? isDocsFixture
                ? "只读观察"
                : "只读 / Demo-only"
              : "只读安全状态不可确认"}
          </dd>
        </div>
        <div>
          <dt>交易许可</dt>
          <dd>否</dd>
        </div>
        <div>
          <dt>交易执行</dt>
          <dd>
            {sourceReadiness.showAsTradable ||
            sourceReadiness.showAsExecutable
              ? "安全阻断"
              : "不可执行"}
          </dd>
        </div>
      </dl>

      <div className="source-readiness-safety-copy">
        <p>非交易许可；非执行指令。</p>
        <p>只展示数据源状态、reader 状态和安全摘要。</p>
      </div>

      <div className="source-readiness-reasons">
        <div>
          <strong>安全阻断原因</strong>
          {renderItems(sourceReadiness.safeBlockReasons, "暂无安全阻断原因。")}
        </div>
        <div>
          <strong>安全警告原因</strong>
          {renderItems(sourceReadiness.safeWarningReasons, "暂无安全警告原因。")}
        </div>
        <div>
          <strong>数据质量备注</strong>
          {renderItems(
            sourceReadiness.safeDataQualityNotes,
            "暂无数据质量备注。",
          )}
        </div>
      </div>
    </section>
  );
}
