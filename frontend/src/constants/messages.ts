export const ERROR_MESSAGES = {
  backendOffline:
    "无法连接后端服务。当前仅显示前端预览内容，不包含真实行情或交易建议。",
  mockMarketUnavailable:
    "无法获取 Mock 行情。当前不显示行情数据，这不是交易信号。",
  placeholderSignalUnavailable:
    "无法获取占位信号。当前不提供任何交易建议。",
  placeholderLogWriteFailed:
    "无法写入占位信号日志。请确认后端已启动；这不是交易操作。",
} as const;

export const ERROR_SAFETY_NOTE =
  "错误状态不影响安全边界：不是真实交易建议，不会自动下单，不会连接真实账户。";
