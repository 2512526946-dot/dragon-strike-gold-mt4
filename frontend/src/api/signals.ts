import { apiGet, getApiBaseUrl } from "./client";

export type PlaceholderSignal = {
  signal_id: string;
  symbol: string;
  source: string;
  timestamp: string;
  action: string;
  signal_type: string;
  lifecycle_status: string;
  market_regime: string;
  final_score: number;
  allow_chasing: boolean;
  risk_level: string;
  leverage_10x_status: string;
  suggested_lot: number;
  is_placeholder: boolean;
  is_tradable: boolean;
  note: string;
};

export type PlaceholderSignalLogResponse = {
  logged: boolean;
  log_id: string;
  created_at: string;
  log_type: string;
  source: string;
  symbol: string;
  signal_id: string;
  action: string;
  signal_type: string;
  lifecycle_status: string;
  is_placeholder: boolean;
  is_tradable: boolean;
  final_score: number;
  suggested_lot: number;
  allow_chasing: boolean;
  note: string;
};

export function fetchPlaceholderSignal(): Promise<PlaceholderSignal> {
  return apiGet<PlaceholderSignal>("/api/signals/placeholder");
}

export async function createPlaceholderSignalLog(): Promise<PlaceholderSignalLogResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/signals/placeholder/log`, {
    method: "POST",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Backend request failed with status ${response.status}`);
  }

  return response.json() as Promise<PlaceholderSignalLogResponse>;
}
