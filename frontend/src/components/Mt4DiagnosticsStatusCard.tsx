import type { Mt4DiagnosticsResponse } from "../api/mt4Diagnostics";

type Mt4DiagnosticsStatusCardProps = {
  diagnostics?: Mt4DiagnosticsResponse | null;
  loading?: boolean;
  error?: string | null;
};

type LayerStatus = {
  label: string;
  statusCode: string;
};

function yesNo(value: boolean) {
  return value ? "是" : "否";
}

function passBlockedUnknown(value: boolean | null) {
  if (value === null) {
    return "未知";
  }

  return value ? "通过" : "阻断";
}

function statusClass(value: boolean | null) {
  if (value === null) {
    return "is-unknown";
  }

  return value ? "is-success" : "is-danger";
}

function buildLayerStatuses(
  diagnostics: Mt4DiagnosticsResponse,
): LayerStatus[] {
  return [
    {
      label: "文件读取",
      statusCode: diagnostics.read_summary.status_code,
    },
    {
      label: "metadata",
      statusCode: diagnostics.metadata_status.status_code,
    },
    {
      label: "freshness",
      statusCode: diagnostics.freshness_status.status_code,
    },
    {
      label: "必需字段",
      statusCode: diagnostics.required_fields_status.status_code,
    },
    {
      label: "字段类型",
      statusCode: diagnostics.field_types_status.status_code,
    },
    {
      label: "数值范围",
      statusCode: diagnostics.numeric_ranges_status.status_code,
    },
    {
      label: "跨字段关系",
      statusCode: diagnostics.cross_field_status.status_code,
    },
  ];
}

export function Mt4DiagnosticsStatusCard({
  diagnostics,
  loading = false,
  error = null,
}: Mt4DiagnosticsStatusCardProps) {
  const gatePassed = diagnostics?.data_quality_passed ?? null;
  const canAnalyze = diagnostics?.can_proceed_to_read_only_analysis ?? null;
  const isTradable = diagnostics?.is_tradable ?? false;
  const layerStatuses = diagnostics ? buildLayerStatuses(diagnostics) : [];

  return (
    <section
      className={`mt4-diagnostics-card ${statusClass(gatePassed)}`}
      aria-label="MT4 只读诊断状态"
    >
      <div className="mt4-diagnostics-header">
        <div>
          <p>Read-only MT4 Diagnostics</p>
          <h2>MT4 只读诊断</h2>
        </div>
        <span>{loading ? "读取中" : passBlockedUnknown(gatePassed)}</span>
      </div>

      {error ? (
        <div className="mt4-diagnostics-empty-state is-error">
          <strong>诊断读取失败</strong>
          <p>{error}</p>
          <p>只读诊断，不是交易许可，不生成交易信号。</p>
        </div>
      ) : null}

      {!error && loading ? (
        <div className="mt4-diagnostics-empty-state">
          <strong>正在读取诊断摘要</strong>
          <p>当前仅等待只读诊断结果，不生成交易信号。</p>
        </div>
      ) : null}

      {!error && !loading && diagnostics ? (
        <>
          <dl className="mt4-diagnostics-summary-grid">
            <div>
              <dt>DataQualityGate</dt>
              <dd>{passBlockedUnknown(gatePassed)}</dd>
            </div>
            <div>
              <dt>可进入只读分析</dt>
              <dd>{yesNo(canAnalyze ?? false)}</dd>
            </div>
            <div>
              <dt>交易许可</dt>
              <dd>{yesNo(isTradable)}</dd>
            </div>
            <div>
              <dt>自动交易</dt>
              <dd>关闭</dd>
            </div>
            <div>
              <dt>status_code</dt>
              <dd>{diagnostics.status_code}</dd>
            </div>
            <div>
              <dt>gate_v1_result.status_code</dt>
              <dd>{diagnostics.gate_v1_result.status_code}</dd>
            </div>
          </dl>

          <dl className="mt4-diagnostics-layer-grid">
            {layerStatuses.map((layer) => (
              <div key={layer.label}>
                <dt>{layer.label}</dt>
                <dd>{layer.statusCode}</dd>
              </div>
            ))}
          </dl>

          <div className="mt4-diagnostics-note">
            <strong>只读说明</strong>
            <p>{diagnostics.note}</p>
            <p>只读诊断，不是交易许可，不生成交易信号。</p>
          </div>
        </>
      ) : null}

      {!error && !loading && !diagnostics ? (
        <div className="mt4-diagnostics-empty-state">
          <strong>暂无诊断摘要</strong>
          <p>只读诊断尚未载入，不生成交易信号。</p>
        </div>
      ) : null}
    </section>
  );
}
