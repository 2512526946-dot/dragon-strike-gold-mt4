import type { PlaceholderSignal } from "../api/signals";
import { ERROR_SAFETY_NOTE } from "../constants/messages";

type PlaceholderSignalStatus =
  | { state: "loading" }
  | { state: "ready"; signal: PlaceholderSignal }
  | { state: "error"; message: string };

type PlaceholderSignalCardProps = {
  status: PlaceholderSignalStatus;
  onRefresh: () => void;
};

export function PlaceholderSignalCard({
  status,
  onRefresh,
}: PlaceholderSignalCardProps) {
  return (
    <section className="signal-card" aria-labelledby="signal-title">
      <div className="signal-card-header">
        <div>
          <p>Placeholder Signal</p>
          <h2 id="signal-title">占位信号预览</h2>
        </div>
        <button type="button" onClick={onRefresh}>
          刷新占位信号
        </button>
      </div>

      {status.state === "ready" ? (
        <>
          <dl className="signal-snapshot-grid">
            <div>
              <dt>signal_id</dt>
              <dd>{status.signal.signal_id}</dd>
            </div>
            <div>
              <dt>symbol</dt>
              <dd>{status.signal.symbol}</dd>
            </div>
            <div>
              <dt>source</dt>
              <dd>{status.signal.source}</dd>
            </div>
            <div>
              <dt>action</dt>
              <dd>{status.signal.action}</dd>
            </div>
            <div>
              <dt>signal_type</dt>
              <dd>{status.signal.signal_type}</dd>
            </div>
            <div>
              <dt>lifecycle_status</dt>
              <dd>{status.signal.lifecycle_status}</dd>
            </div>
            <div>
              <dt>market_regime</dt>
              <dd>{status.signal.market_regime}</dd>
            </div>
            <div>
              <dt>final_score</dt>
              <dd>{status.signal.final_score}</dd>
            </div>
            <div>
              <dt>allow_chasing</dt>
              <dd>{String(status.signal.allow_chasing)}</dd>
            </div>
            <div>
              <dt>risk_level</dt>
              <dd>{status.signal.risk_level}</dd>
            </div>
            <div>
              <dt>leverage_10x_status</dt>
              <dd>{status.signal.leverage_10x_status}</dd>
            </div>
            <div>
              <dt>suggested_lot</dt>
              <dd>{status.signal.suggested_lot}</dd>
            </div>
            <div>
              <dt>is_placeholder</dt>
              <dd>{String(status.signal.is_placeholder)}</dd>
            </div>
            <div>
              <dt>is_tradable</dt>
              <dd>{String(status.signal.is_tradable)}</dd>
            </div>
            <div>
              <dt>timestamp</dt>
              <dd>{status.signal.timestamp}</dd>
            </div>
          </dl>
          <p className="signal-note">{status.signal.note}</p>
        </>
      ) : (
        <div className="signal-empty-state">
          <strong>{status.state === "loading" ? "读取中" : "无法获取"}</strong>
          <p>
            {status.state === "loading"
              ? "正在读取占位信号。"
              : status.message}
          </p>
          {status.state === "error" ? <p>{ERROR_SAFETY_NOTE}</p> : null}
        </div>
      )}

      <p className="signal-safety-note">
        当前为开发占位信号，不是真实交易建议，不可用于下单。
      </p>
    </section>
  );
}
