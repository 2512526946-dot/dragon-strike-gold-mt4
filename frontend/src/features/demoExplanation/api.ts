import { apiGet } from "../../api/client";
import { DEMO_READONLY_EXPLANATION_ENDPOINT } from "./contracts";
import {
  apiErrorViewModel,
  mapDemoReadOnlyExplanationApiToViewModel,
} from "./mapper";
import type {
  DemoReadOnlyExplanationApiResponse,
  DemoReadOnlyExplanationViewModel,
} from "./types";

export async function fetchDemoReadOnlyExplanation(): Promise<DemoReadOnlyExplanationViewModel> {
  try {
    const response = await apiGet<DemoReadOnlyExplanationApiResponse>(
      DEMO_READONLY_EXPLANATION_ENDPOINT,
    );
    return mapDemoReadOnlyExplanationApiToViewModel(response);
  } catch {
    return apiErrorViewModel();
  }
}
