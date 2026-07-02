const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  return (configuredBaseUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

export async function apiGet<TResponse>(path: string): Promise<TResponse> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const response = await fetch(`${getApiBaseUrl()}${normalizedPath}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Backend request failed with status ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}
