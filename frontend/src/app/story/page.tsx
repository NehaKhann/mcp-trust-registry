"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type ScanRecord } from "@/lib/api";
import { GradeBadge } from "@/components/GradeBadge";
import { safeParseArray } from "@/lib/format";

export default function StoryPage() {
  const [scan, setScan] = useState<ScanRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .history("evil-calculator", "calculate")
      .then((rows) => setScan(rows[rows.length - 1]))
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-lg border border-grade-f/30 bg-grade-f-soft px-4 py-3 text-sm text-grade-f">
        Couldn&apos;t load the example scan — run{" "}
        <code className="font-mono">python scan_live.py evil-calculator</code> first, then reload.
      </div>
    );
  }

  if (!scan) {
    return <div className="h-96 animate-pulse rounded-xl bg-surface-raised" />;
  }

  const behaviorFlags = scan.behavior_flags ? safeParseArray(scan.behavior_flags) : [];

  return (
    <div className="mx-auto max-w-2xl">
      <div className="kicker mb-2 font-mono text-xs uppercase tracking-wide text-accent-ink">
        A real scenario, real data
      </div>
      <h1 className="text-3xl font-semibold tracking-tight text-balance">
        Sam almost trusted a calculator.
      </h1>
      <p className="mt-4 text-text-muted">
        Sam is a developer setting up an AI assistant. Someone online shares a small MCP tool — just
        a calculator, nothing special. Before connecting it to anything real, Sam checks it here
        first. Everything below is the actual scan this registry ran, not a mockup.
      </p>

      <div className="mt-12 space-y-10">
        <Beat n="1" title="The tool Sam found">
          <p className="mb-3 text-sm text-text-muted">Its entire declared description:</p>
          <p className="rounded-lg bg-surface-raised px-4 py-3.5 font-mono text-sm text-text">
            &ldquo;{scan.description}&rdquo;
          </p>
          <p className="mt-3 text-sm text-text-faint">
            Nothing alarming. Nothing unusual. Exactly what you&apos;d expect from a calculator.
          </p>
        </Beat>

        <Beat n="2" title="The static checks came back clean">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-border bg-surface p-4">
              <div className="mb-1 text-xs font-medium uppercase tracking-wide text-text-faint">
                Rule-based engine
              </div>
              <div className="font-mono text-lg text-grade-a">{scan.rule_score}/100</div>
              <div className="mt-1 text-xs text-text-faint">no known-dangerous patterns matched</div>
            </div>
            <div className="rounded-lg border border-border bg-surface p-4">
              <div className="mb-1 text-xs font-medium uppercase tracking-wide text-text-faint">
                AI engine
              </div>
              <div className="font-mono text-lg text-grade-a">{scan.llm_risk_level}</div>
              <div className="mt-1 text-xs text-text-faint">no phrases suggesting undisclosed actions</div>
            </div>
          </div>
          <p className="mt-3 text-sm text-text-faint">
            Both engines agreed: this looks completely safe. If Sam stopped here, this tool would be
            sitting in their AI assistant right now.
          </p>
        </Beat>

        <Beat n="3" title="But Sam ran it in the sandbox first">
          <p className="text-sm text-text-muted">
            Launched inside Docker, no internet access, one test call: <i>add 2 and 3</i>. It answered
            correctly — <span className="font-mono text-text">5</span>. Everything looked completely
            normal. Then Sam checked what had changed on disk while it was running.
          </p>
        </Beat>

        <Beat n="4" title="One file that was never supposed to exist" danger>
          {behaviorFlags.length > 0 ? (
            <ul className="space-y-1.5">
              {behaviorFlags.map((f, i) => (
                <li key={i} className="rounded bg-grade-f-soft px-3 py-2 font-mono text-sm text-grade-f">
                  {f}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">(no violation recorded on this scan)</p>
          )}
          <p className="mt-3 text-sm text-text-muted">
            A calculator has no legitimate reason to touch any file. This one quietly copied a planted
            secret into a disguised backup the instant it was called — invisible from the outside,
            since it still answered the math question correctly.
          </p>
        </Beat>

        <Beat n="5" title="Verdict">
          <div className="flex items-start gap-4">
            <GradeBadge grade={scan.grade} size="lg" />
            <p className="text-sm text-text-muted">
              A tool that passed every text-based check failed the only check that mattered: what it
              actually does. This is why every tool in this registry gets checked both ways — and why
              Sam didn&apos;t connect it.
            </p>
          </div>
        </Beat>
      </div>

      <div className="mt-14 flex flex-wrap items-center gap-3 border-t border-border pt-8">
        <Link
          href="/scan"
          className="rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-accent-contrast transition-opacity hover:opacity-90"
        >
          Check a tool yourself →
        </Link>
        <Link
          href="/tool/evil-calculator/calculate"
          className="rounded-lg border border-border px-4 py-2.5 text-sm text-text-muted transition-colors hover:text-text hover:border-text-faint"
        >
          See the full report
        </Link>
      </div>
    </div>
  );
}

function Beat({
  n,
  title,
  danger,
  children,
}: {
  n: string;
  title: string;
  danger?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-4">
      <div
        className={`flex h-7 w-7 flex-none items-center justify-center rounded-full font-mono text-xs font-semibold ${
          danger ? "bg-grade-f-soft text-grade-f" : "bg-accent-soft text-accent-ink"
        }`}
      >
        {n}
      </div>
      <div className="min-w-0 flex-1">
        <h2 className="mb-2.5 font-semibold text-text">{title}</h2>
        {children}
      </div>
    </div>
  );
}
