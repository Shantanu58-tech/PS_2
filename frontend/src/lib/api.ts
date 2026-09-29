export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type HealthStatus = {
  status: "ok";
  service: string;
  version: string;
  mode: "replay" | "live";
  env: string;
  time_utc: string;
};

export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/healthz`, { cache: "no-store", signal });
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return (await response.json()) as HealthStatus;
}
