"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type LeaderboardRow } from "@/lib/api";

export default function LandingPage() {
  const [stats, setStats] = useState<{ tools: number; scans: number; flagged: number } | null>(null);

  useEffect(() => {
    api
      .leaderboard()
      .then((rows: LeaderboardRow[]) => {
        setStats({
          tools: rows.length,
          scans: rows.reduce((sum, r) => sum + r.scan_count, 0),
          flagged: rows.filter((r) => r.grade === "F").length,
        });
      })
      .catch(() => setStats(null));
  }, []);

  return (
    <div>
      {/* ---------- hero ---------- */}
      <section className="py-8 sm:py-14">
        <div className="kicker mb-4 font-mono text-xs uppercase tracking-wide text-accent-ink">
          Model Context Protocol · trust registry
        </div>
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          An honest description isn&apos;t proof of honest code.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-text-muted">
          Before you connect a new MCP tool to your AI assistant, check it two ways — what it{" "}
          <i>claims</i> to do, and what it <i>actually does</i> when run in an isolated,
          network-blocked sandbox.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            href="/scan"
            className="rounded-lg bg-accent px-5 py-3 text-sm font-medium text-accent-contrast transition-opacity hover:opacity-90"
          >
            Scan a tool →
          </Link>
          <Link
            href="/registry"
            className="rounded-lg border border-border px-5 py-3 text-sm text-text-muted transition-colors hover:text-text hover:border-text-faint"
          >
            Browse the registry
          </Link>
        </div>

        {stats && stats.tools > 0 && (
          <div className="mt-10 flex flex-wrap gap-x-8 gap-y-3 border-t border-border pt-6">
            <Stat value={stats.tools} label="tools tracked" />
            <Stat value={stats.scans} label="scans run" />
            <Stat value={stats.flagged} label="flagged high-risk" tone={stats.flagged > 0 ? "grade-f" : undefined} />
          </div>
        )}
      </section>

      {/* ---------- the catch, as proof not just a claim ---------- */}
      <section className="mb-16 rounded-2xl border border-border bg-surface p-6 sm:p-8">
        <div className="grid gap-6 sm:grid-cols-[1fr_auto] sm:items-center">
          <div>
            <div className="mb-2 font-mono text-xs uppercase tracking-wide text-text-faint">
              A real result, not a mockup
            </div>
            <p className="text-lg text-text">
              A tool description read as <b className="text-grade-a">clean</b> to a rule engine and
              an AI model — <i>&ldquo;no phrases suggesting undisclosed actions.&rdquo;</i>{" "}
              The sandbox caught it copying a planted secret into a disguised file the instant it ran.
              Grade: <b className="text-grade-f">F</b>.
            </p>
          </div>
          <Link
            href="/story"
            className="whitespace-nowrap rounded-lg border border-border px-5 py-3 text-center text-sm font-medium text-text transition-colors hover:border-accent hover:text-accent-ink"
          >
            Read the full story →
          </Link>
        </div>
      </section>

      {/* ---------- how it works ---------- */}
      <section className="mb-16">
        <h2 className="mb-1 text-xl font-semibold tracking-tight">Three checks, never blended into one score</h2>
        <p className="mb-8 max-w-2xl text-text-muted">
          Each engine&apos;s verdict is shown on its own — you can always see exactly which part of a
          grade came from reading words versus watching actions.
        </p>
        <div className="grid gap-4 sm:grid-cols-3">
          <EngineCard
            n="01"
            title="Rule-based engine"
            body="Plain code checking for known-dangerous patterns — hidden-instruction phrasing, credential references, fake system tags. Fast and predictable, but only ever catches what it was written to look for."
          />
          <EngineCard
            n="02"
            title="AI semantic engine"
            body="A model reads the description and judges intent — catching the cases fixed rules miss, like scope creep buried in otherwise-reasonable prose. Forced into structured output, never free-form opinion."
          />
          <EngineCard
            n="03"
            title="Docker sandbox"
            body="Runs the real server, network-blocked, and diffs the filesystem before and after every call. Catches what perfect wording can't hide, because it never reads the description at all."
          />
        </div>
      </section>

      {/* ---------- before you install ---------- */}
      <section className="mb-16 grid gap-8 sm:grid-cols-2 sm:items-center">
        <div>
          <h2 className="mb-3 text-xl font-semibold tracking-tight">
            Before <code className="font-mono text-lg">git clone</code>, not after
          </h2>
          <p className="text-text-muted">
            Found a new MCP server on GitHub or npm? Paste its declared tools in, or give it a real
            package name and let the sandbox build and run it live — before that code ever touches
            your machine for real.
          </p>
          <Link href="/scan" className="mt-4 inline-block text-sm font-medium text-accent-ink hover:underline">
            Try it now →
          </Link>
        </div>
        <div className="rounded-xl border border-border bg-surface-raised p-5 font-mono text-xs text-text-muted">
          <div className="mb-2 text-text-faint"># the same check, from a terminal</div>
          <div className="text-text">cd scanner</div>
          <div className="text-text">python scan_package.py @scope/some-mcp-server</div>
          <div className="mt-3 text-grade-a">✓ Built and ran sandbox image (--network none)</div>
          <div className="text-grade-a">✓ Declared 6 real tools, graded</div>
        </div>
      </section>

      {/* ---------- footer cta ---------- */}
      <section className="border-t border-border py-10 text-center">
        <p className="mb-4 text-text-muted">Zero-cost by design — local Ollama or Groq&apos;s free tier, self-hosted Docker sandbox, no paid API required.</p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/registry"
            className="rounded-lg bg-accent px-5 py-3 text-sm font-medium text-accent-contrast transition-opacity hover:opacity-90"
          >
            Browse the registry →
          </Link>
        </div>
      </section>
    </div>
  );
}

function Stat({ value, label, tone }: { value: number; label: string; tone?: string }) {
  return (
    <div>
      <div className={`font-mono text-2xl font-semibold tabular-nums ${tone ? `text-${tone}` : "text-text"}`}>
        {value}
      </div>
      <div className="text-xs text-text-faint">{label}</div>
    </div>
  );
}

function EngineCard({ n, title, body }: { n: string; title: string; body: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="mb-3 font-mono text-xs text-text-faint">{n}</div>
      <h3 className="mb-2 font-medium text-text">{title}</h3>
      <p className="text-sm text-text-muted">{body}</p>
    </div>
  );
}
