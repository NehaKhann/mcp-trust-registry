"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type ScanRecord } from "@/lib/api";
import { GradeBadge, GradeLabel } from "@/components/GradeBadge";
import { SourceBadge } from "@/components/SourceBadge";
import { timeAgo, safeParseArray } from "@/lib/format";

export default function ToolDetailPage() {
  const params = useParams<{ server: string; tool: string }>();
  const server = decodeURIComponent(params.server);
  const tool = decodeURIComponent(params.tool);

  const [scans, setScans] = useState<ScanRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .history(server, tool)
      .then(setScans)
      .catch((e) => setError(e.message));
  }, [server, tool]);

  if (error) {
    return (
      <div className="rounded-lg border border-grade-f/30 bg-grade-f-soft px-4 py-3 text-sm text-grade-f">
        {error}
      </div>
    );
  }

  if (!scans) {
    return <div className="h-40 animate-pulse rounded-xl bg-surface-raised" />;
  }

  const latest = scans[scans.length - 1];
  const ruleFlags = safeParseArray(latest.rule_flags);
  const llmPhrases = safeParseArray(latest.llm_flagged_phrases);
  const behaviorFlags = latest.behavior_flags ? safeParseArray(latest.behavior_flags) : [];

  return (
    <div>
      <Link href="/" className="mb-6 inline-flex items-center gap-1 text-sm text-text-muted hover:text-text">
        ← Registry
      </Link>

      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{server}</h1>
          <div className="mt-0.5 font-mono text-sm text-text-faint">{tool}</div>
        </div>
        <div className="flex items-center gap-3">
          <GradeBadge grade={latest.grade} size="lg" />
          <GradeLabel grade={latest.grade} />
        </div>
      </div>

      <div className="mb-8">
        <SourceBadge source={latest.source} />
      </div>

      {behaviorFlags.length > 0 && (
        <div className="mb-8 rounded-xl border border-grade-f/40 bg-grade-f-soft px-5 py-4">
          <div className="mb-2 flex items-center gap-2 font-semibold text-grade-f">
            <span>⚠</span> Behavioral violation caught in sandbox
          </div>
          <p className="mb-2 text-sm text-text">
            This tool&apos;s description read as safe to the static engines above — the grade was overridden to{" "}
            <b>F</b> because of what it actually did when run in an isolated, network-blocked container:
          </p>
          <ul className="space-y-1">
            {behaviorFlags.map((f, i) => (
              <li key={i} className="font-mono text-xs text-grade-f">
                • {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Section title="Current declared description">
        <p className="rounded-lg bg-surface-raised px-4 py-3.5 font-mono text-sm leading-relaxed text-text">
          &ldquo;{latest.description}&rdquo;
        </p>
      </Section>

      <div className="grid grid-cols-2 gap-4">
        <Section title="Rule-based engine">
          <div className="mb-2 font-mono text-sm text-text-muted">Risk score: {latest.rule_score}/100</div>
          {ruleFlags.length === 0 ? (
            <div className="text-sm text-text-faint">No known-dangerous patterns matched.</div>
          ) : (
            <ul className="space-y-1.5">
              {ruleFlags.map((f, i) => (
                <li key={i} className="flex gap-2 text-sm text-grade-f">
                  <span>⚠</span>
                  <span className="text-text">{f}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="AI engine (semantic)">
          <div className="mb-2 font-mono text-sm text-text-muted">Risk level: {latest.llm_risk_level ?? "—"}</div>
          {llmPhrases.length > 0 && (
            <ul className="mb-2 space-y-1.5">
              {llmPhrases.map((p, i) => (
                <li key={i} className="rounded bg-grade-f-soft px-2 py-1 font-mono text-xs text-grade-f">
                  &ldquo;{p}&rdquo;
                </li>
              ))}
            </ul>
          )}
          {latest.llm_reasoning && <p className="text-sm text-text-muted">{latest.llm_reasoning}</p>}
        </Section>
      </div>

      <Section title={`Timeline (${scans.length} scan${scans.length === 1 ? "" : "s"})`}>
        <ol className="space-y-0">
          {[...scans].reverse().map((s, i, arr) => {
            const prev = arr[i + 1];
            const changed = prev && prev.grade !== s.grade;
            return (
              <li key={s.id} className="flex items-center gap-3 border-b border-border py-3 last:border-0">
                <GradeBadge grade={s.grade} size="sm" />
                <div className="flex-1">
                  <div className="text-sm text-text">{timeAgo(s.scanned_at)}</div>
                  <div className="text-xs text-text-faint">{s.scanned_at.slice(0, 19).replace("T", " ")}</div>
                </div>
                {changed && (
                  <span className="rounded-full bg-grade-f-soft px-2.5 py-1 font-mono text-xs font-medium text-grade-f">
                    CHANGED from {prev.grade}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <h2 className="mb-2.5 text-xs font-medium uppercase tracking-wide text-text-faint">{title}</h2>
      {children}
    </div>
  );
}
