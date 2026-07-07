import type { DemoReadOnlyExplanationComponentViewModel } from "../types";

type ExplanationComponentListProps = {
  components: DemoReadOnlyExplanationComponentViewModel[];
};

function listText(values: string[]): string {
  return values.length > 0 ? values.join("；") : "无";
}

export function ExplanationComponentList({
  components,
}: ExplanationComponentListProps) {
  return (
    <section
      className="demo-diagnostics-card"
      aria-labelledby="demo-explanation-components-title"
    >
      <div className="demo-diagnostics-section-heading">
        <p>Component Explanations</p>
        <h3 id="demo-explanation-components-title">组件只读解释</h3>
      </div>
      {components.length > 0 ? (
        <ul className="demo-diagnostics-component-list">
          {components.map((component) => (
            <li key={component.componentName}>
              <div className="demo-diagnostics-component-header">
                <strong>{component.componentName}</strong>
                <span>{component.status}</span>
              </div>
              <p>{component.plainLanguageSummary}</p>
              <p>展示影响：{component.userImpact}</p>
              <p>安全下一步：{component.safeNextStep || "查看只读解释。"}</p>
              <p>
                禁止误解：
                {component.forbiddenInterpretation ||
                  "不能解释为交易许可或执行指令。"}
              </p>
              <p>
                阻断说明：
                {listText(component.blockReasonsExplained)}
              </p>
              <p>
                警告说明：
                {listText(component.warningReasonsExplained)}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="demo-diagnostics-empty-state">
          <strong>暂无组件只读解释</strong>
          <p>当前没有可展示的组件解释内容。</p>
        </div>
      )}
    </section>
  );
}
