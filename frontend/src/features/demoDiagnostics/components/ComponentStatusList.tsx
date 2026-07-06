import type { ComponentStatusViewModel } from "../types";

type ComponentStatusListProps = {
  components: ComponentStatusViewModel[];
};

function reasonText(values: string[]) {
  return values.length > 0 ? values.join("；") : "无";
}

export function ComponentStatusList({ components }: ComponentStatusListProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-diagnostics-components-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Component Status List</p>
        <h3 id="demo-diagnostics-components-title">组件安全摘要</h3>
      </div>
      {components.length > 0 ? (
        <ul className="demo-diagnostics-component-list">
          {components.map((component) => (
            <li key={component.component_name}>
              <div className="demo-diagnostics-component-header">
                <strong>{component.component_name}</strong>
                <span>{component.status}</span>
              </div>
              <dl>
                <div>
                  <dt>status_code</dt>
                  <dd>{component.status_code}</dd>
                </div>
                <div>
                  <dt>safe count</dt>
                  <dd>{component.safe_count}</dd>
                </div>
              </dl>
              <p>{component.safe_summary}</p>
              <p>block_reasons：{reasonText(component.block_reasons)}</p>
              <p>warning_reasons：{reasonText(component.warning_reasons)}</p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="demo-diagnostics-empty-state">
          <strong>暂无组件摘要</strong>
          <p>当前没有可展示的只读组件状态。</p>
        </div>
      )}
    </section>
  );
}
