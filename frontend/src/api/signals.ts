import { apiGet } from "./client";

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

export function fetchPlaceholderSignal(): Promise<PlaceholderSignal> {
  return apiGet<PlaceholderSignal>("/api/signals/placeholder");
}
