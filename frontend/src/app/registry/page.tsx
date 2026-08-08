"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, type LeaderboardRow } from "@/lib/api";
import { GradeBadge } from "@/components/GradeBadge";
import { SourceBadge } from "@/components/SourceBadge";
import { timeAgo } from "@/lib/format";

export default function RegistryPage() {
  const [rows, setRows] = useState<LeaderboardRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api
      .leaderboard()
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);

  const filtered = useMemo(() => {
    if (!rows) return [];
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(
      (r) => r.server_name.toLowerCase().includes(q) || r.tool_name.toLowerCase().includes(q)
    );
  }, [rows, query]);

  const stats = useMemo(() => {
    if (!rows) return null;
    const flagged = rows.filter((r) => r.grade === "F").length;
    const totalScans = rows.reduce((sum, r) => sum + r.scan_count, 0);
    return { servers: rows.length, flagged, totalScans };
  }, [rows]);

  return (
    <div>
      <div className="mb-8 flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Registry</h1>
        <p className="text-text-muted">
          Every MCP tool that&apos;s been checked so far — declared behavior vs. what the scanners
          actually found, with a full history per tool.
        </p>
      </div>

      {stats && (
        <div className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatCard label="Tools tracked" value={stats.servers} />
          <StatCard label="Total scans" value={stats.totalScans} />
          <StatCard label="Flagged high-risk" value={stats.flagged} tone={stats.flagged > 0 ? "grade-f" : undefined} />
        </div>
      )}

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by server or tool name…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-accent/40"
        />
      </div>

      {error && (
        <div className="rounded-lg border border-grade-f/30 bg-grade-f-soft px-4 py-3 text-sm text-grade-f">
          Couldn&apos;t reach the API at localhost:8001 — is <code className="font-mono">uvicorn main:app</code> running?
          <div className="mt-1 text-text-muted">{error}</div>
        </div>
      )}

      {!error && rows === null && <LeaderboardSkeleton />}

      {!error && rows !== null && rows.length === 0 && (
        <EmptyState />
      )}

      {!error && rows !== null && rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-raised text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-4 py-3 font-medium">Server / Tool</th>
                <th className="px-4 py-3 font-medium">Grade</th>
                <th className="px-4 py-3 font-medium">Verification</th>
                <th className="px-4 py-3 font-medium">Scans</th>
                <th className="px-4 py-3 font-medium">Last checked</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={`${r.server_name}/${r.tool_name}`} className="border-b border-border last:border-0">
                  <td className="px-0 py-0">
                    <Link
                      href={`/tool/${encodeURIComponent(r.server_name)}/${encodeURIComponent(r.tool_name)}`}
                      className="block px-4 py-3.5 transition-colors hover:bg-surface-raised"
                    >
                      <div className="font-medium text-text">{r.server_name}</div>
                      <div className="font-mono text-xs text-text-faint">{r.tool_name}</div>
                    </Link>
                  </td>
                  <td className="px-4 py-3.5">
                    <GradeBadge grade={r.grade} size="sm" />
                  </td>
                  <td className="px-4 py-3.5">
                    <SourceBadge source={r.source} />
                  </td>
                  <td className="px-4 py-3.5 tabular-nums text-text-muted">{r.scan_count}</td>
                  <td className="px-4 py-3.5 text-text-muted">{timeAgo(r.scanned_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface px-4 py-3.5">
      <div className={`font-mono text-2xl font-semibold tabular-nums ${tone ? `text-${tone}` : "text-text"}`}>
        {value}
      </div>
      <div className="mt-0.5 text-xs text-text-muted">{label}</div>
    </div>
  );
}

function LeaderboardSkeleton() {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 border-b border-border px-4 py-4 last:border-0">
          <div className="h-4 w-40 animate-pulse rounded bg-surface-raised" />
          <div className="h-6 w-6 animate-pulse rounded bg-surface-raised" />
          <div className="h-4 w-16 animate-pulse rounded bg-surface-raised" />
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border py-16 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-raised text-text-faint">
        ?
      </div>
      <div>
        <div className="font-medium text-text">Nothing scanned yet</div>
        <p className="mt-1 max-w-sm text-sm text-text-muted">
          Run the CLI (<code className="font-mono">python scan.py …</code>) or use{" "}
          <Link href="/scan" className="text-accent hover:underline">
            Scan a tool
          </Link>{" "}
          to add the first entry to the registry.
        </p>
      </div>
    </div>
  );
}
