import type { MarketSnapshot } from "../api/market";

type MarketSnapshotStatus =
  | { state: "loading" }
  | { state: "ready"; snapshot: MarketSnapshot }
  | { state: "error"; message: string };

type MarketSnapshotCardProps = {
  status: MarketSnapshotStatus;
  onRefresh: () => void;
};

export function MarketSnapshotCard({
  status,
  onRefresh,
}: MarketSnapshotCardProps) {
  return (
    <section className="market-card" aria-labelledby="market-title">
      <div className="market-card-header">
        <div>
          <p>Mock Market Snapshot</p>
          <h2 id="market-title">Mock 黄金行情快照</h2>
        </div>
        <button type="button" onClick={onRefresh}>
          刷新 Mock 行情
        </button>
      </div>

      {status.state === "ready" ? (
        <>
          <dl className="market-snapshot-grid">
            <div>
              <dt>symbol</dt>
              <dd>{status.snapshot.symbol}</dd>
            </div>
            <div>
              <dt>bid</dt>
              <dd>{status.snapshot.bid.toFixed(status.snapshot.digits)}</dd>
            </div>
            <div>
              <dt>ask</dt>
              <dd>{status.snapshot.ask.toFixed(status.snapshot.digits)}</dd>
            </div>
            <div>
              <dt>spread</dt>
              <dd>{status.snapshot.spread.toFixed(status.snapshot.digits)}</dd>
            </div>
            <div>
              <dt>spread_points</dt>
              <dd>{status.snapshot.spread_points}</dd>
            </div>
            <div>
              <dt>source</dt>
              <dd>{status.snapshot.source}</dd>
            </div>
            <div>
              <dt>data_status</dt>
              <dd>{status.snapshot.data_status}</dd>
            </div>
            <div>
              <dt>is_mock</dt>
              <dd>{String(status.snapshot.is_mock)}</dd>
            </div>
            <div>
              <dt>is_tradable</dt>
              <dd>{String(status.snapshot.is_tradable)}</dd>
            </div>
            <div>
              <dt>timestamp</dt>
              <dd>{status.snapshot.timestamp}</dd>
            </div>
          </dl>
          <p className="market-note">{status.snapshot.note}</p>
        </>
      ) : (
        <div className="market-empty-state">
          <strong>{status.state === "loading" ? "读取中" : "无法获取"}</strong>
          <p>
            {status.state === "loading"
              ? "正在读取 Mock 行情快照。"
              : status.message}
          </p>
        </div>
      )}

      <p className="market-safety-note">
        当前为开发模拟行情，不是真实行情，不是交易信号，不可用于下单。
      </p>
    </section>
  );
}
