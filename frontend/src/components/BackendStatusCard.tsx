import type { HealthResponse } from "../api/health";
import { ERROR_SAFETY_NOTE } from "../constants/messages";

type BackendStatus =
  | { state: "loading" }
  | { state: "online"; health: HealthResponse }
  | { state: "offline"; message: string };

type BackendStatusCardProps = {
  status: BackendStatus;
};

export function BackendStatusCard({ status }: BackendStatusCardProps) {
  if (status.state === "online") {
    return (
      <section className="backend-status-card is-online" aria-label="后端连接状态">
        <div className="backend-status-header">
          <span>后端状态</span>
          <strong>在线</strong>
        </div>
        <dl className="backend-health-list">
          <div>
            <dt>project</dt>
            <dd>{status.health.project}</dd>
          </div>
          <div>
            <dt>name</dt>
            <dd>{status.health.name}</dd>
          </div>
          <div>
            <dt>version</dt>
            <dd>{status.health.version}</dd>
          </div>
          <div>
            <dt>stage</dt>
            <dd>{status.health.stage}</dd>
          </div>
        </dl>
      </section>
    );
  }

  const value = status.state === "loading" ? "检测中" : "离线";
  const message =
    status.state === "loading"
      ? "正在读取后端 /health。"
      : status.message;

  return (
    <section className="backend-status-card is-offline" aria-label="后端连接状态">
      <div className="backend-status-header">
        <span>后端状态</span>
        <strong>{value}</strong>
      </div>
      <p>{message}</p>
      {status.state === "offline" ? <p>{ERROR_SAFETY_NOTE}</p> : null}
    </section>
  );
}
