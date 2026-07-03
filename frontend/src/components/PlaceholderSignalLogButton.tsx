import type { MouseEventHandler } from "react";

type PlaceholderSignalLogButtonProps = {
  disabled?: boolean;
  loading?: boolean;
  label?: string;
  helperText?: string;
  onClick?: MouseEventHandler<HTMLButtonElement>;
};

const DEFAULT_LABEL = "记录占位信号";
const DEFAULT_HELPER_TEXT =
  "仅用于开发阶段记录占位信号，不是交易按钮，不会下单，不会连接真实账户。";
const DEVELOPMENT_NOTE =
  "后续接入时只触发占位信号日志，不代表真实信号或交易建议。";

export function PlaceholderSignalLogButton({
  disabled = false,
  loading = false,
  label = DEFAULT_LABEL,
  helperText = DEFAULT_HELPER_TEXT,
  onClick,
}: PlaceholderSignalLogButtonProps) {
  const isDisabled = disabled || loading || !onClick;

  return (
    <div
      className="placeholder-signal-log-control"
      aria-label="占位信号日志记录控件"
    >
      <button
        type="button"
        disabled={isDisabled}
        aria-busy={loading}
        onClick={onClick}
      >
        {loading ? "记录中..." : label}
      </button>
      <p>{helperText}</p>
      <p>{DEVELOPMENT_NOTE}</p>
    </div>
  );
}
