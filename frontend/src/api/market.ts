import { apiGet } from "./client";

export type MarketSnapshot = {
  symbol: string;
  source: string;
  timestamp: string;
  bid: number;
  ask: number;
  spread: number;
  spread_points: number;
  digits: number;
  data_status: string;
  is_mock: boolean;
  is_tradable: boolean;
  note: string;
};

export function fetchMarketSnapshot(): Promise<MarketSnapshot> {
  return apiGet<MarketSnapshot>("/api/market/snapshot");
}
