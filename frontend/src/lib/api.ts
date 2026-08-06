const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export type Grade = "A" | "B" | "C" | "F";

export type ScanSource = "manual" | "docker-sandbox";

export type LeaderboardRow = {
  server_name: string;
  tool_name: string;
  grade: Grade;
  scan_count: number;
  scanned_at: string;
  source: ScanSource;
};

export type ScanRecord = {
  id: number;
  server_name: string;
  tool_name: string;
  description: string;
  rule_score: number;
  rule_flags: string; // JSON-encoded string[]
  llm_risk_level: string | null;
  llm_targets_model: string | null;
  llm_flagged_phrases: string; // JSON-encoded string[]
  llm_reasoning: string | null;
  grade: Grade;
  scanned_at: string;
  source: ScanSource;
  behavior_flags: string | null; // JSON-encoded string[], only set on a sandbox-caught violation
};

export type ScanResponse = {
  scan_id: number;
  server_name: string;
  tool_name: string;
  description: string;
  grade: Grade;
  rule_result: { engine: string; risk_score: number; flags: { reason: string }[] };
  llm_result: {
    engine: string;
    risk_level?: string;
    targets_the_model?: boolean | null;
    flagged_phrases?: string[];
    reasoning?: string;
    error?: string;
  };
  previous_grade: Grade | null;
  grade_changed: boolean;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  leaderboard: () => request<LeaderboardRow[]>("/api/leaderboard"),
  history: (server: string, tool: string) =>
    request<ScanRecord[]>(`/api/history/${encodeURIComponent(server)}/${encodeURIComponent(tool)}`),
  scan: (payload: { server_name: string; tool_name: string; description: string }) =>
    request<ScanResponse>("/api/scan", { method: "POST", body: JSON.stringify(payload) }),
};
