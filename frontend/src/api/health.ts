import { apiGet } from "./client";

export type HealthResponse = {
  project: string;
  name: string;
  status: string;
  version: string;
  stage: string;
};

export function fetchHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
