import { apiGet } from "../../api/client";
import { DEMO_DIAGNOSTICS_ENDPOINT } from "./contracts";
import { mapDemoDiagnosticsApiToViewModel } from "./mapper";
import type {
  DemoDiagnosticsApiResponse,
  DemoDiagnosticsViewModel,
} from "./types";

export async function getDemoReadOnlyDiagnostics(): Promise<DemoDiagnosticsViewModel> {
  const response = await apiGet<DemoDiagnosticsApiResponse>(
    DEMO_DIAGNOSTICS_ENDPOINT,
  );
  return mapDemoDiagnosticsApiToViewModel(response);
}
