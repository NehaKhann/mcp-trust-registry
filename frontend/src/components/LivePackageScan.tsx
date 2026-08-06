"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type PackageScanResult } from "@/lib/api";
import { GradeBadge } from "@/components/GradeBadge";

export function LivePackageScan() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [packageName, setPackageName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PackageScanResult | null>(null);

  useEffect(() => {
    api
      .health()
      .then((h) => setEnabled(h.live_package_scan_enabled))
      .catch(() => setEnabled(false));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.scanPackage({ package_name: packageName });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  if (enabled === null) {
    return <div className="h-40 animate-pulse rounded-xl bg-surface-raised" />;
  }

  if (!enabled) {
    return (
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-2 font-medium text-text">Live package scanning is off on this deployment</div>
        <p className="mb-4 text-sm text-text-muted">
          This mode actually downloads and runs a real npm package inside Docker — a real action, not
          just a text check, so it&apos;s disabled by default anywhere this site is reachable by
          strangers. Run it yourself instead:
        </p>
        <pre className="overflow-x-auto rounded-lg bg-surface-raised px-4 py-3 font-mono text-xs text-text">
          cd scanner{"\n"}python scan_package.py &lt;npm-package-name&gt;
        </pre>
        <p className="mt-4 text-xs text-text-faint">
          Running your own copy of this site locally? Start the API with{" "}
          <code className="font-mono">ALLOW_LIVE_PACKAGE_SCAN=true</code> to turn this on.
        </p>
      </div>
    );
  }

  return (
    <div>
      <p className="mb-4 text-sm text-text-muted">
        Give it a real npm package name for an MCP server. It downloads the real package, builds a
        fresh sandbox image, runs it with <code className="font-mono text-xs">--network none</code>,
        and grades every tool it actually declares — the same thing{" "}
        <code className="font-mono text-xs">scan_package.py</code> does from a terminal, triggered from
        here instead.
      </p>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          required
          value={packageName}
          onChange={(e) => setPackageName(e.target.value)}
          placeholder="e.g. @modelcontextprotocol/server-memory"
          className="flex-1 rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm font-mono placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-accent/40"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-accent-contrast transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Building sandbox…" : "Scan package (sandboxed)"}
        </button>
      </form>

      {loading && (
        <p className="mt-3 text-xs text-text-faint">
          This can take up to a minute — downloading the real package, building a Docker image, then
          running it network-blocked. Not a mistake if it feels slower than the text-only scan.
        </p>
      )}

      {error && (
        <div className="mt-6 rounded-lg border border-grade-f/30 bg-grade-f-soft px-4 py-3 text-sm text-grade-f">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8">
          <div className="mb-4 rounded-xl border border-border bg-surface p-5">
            <div className="font-medium text-text">{result.package_name}</div>
            <div className="mt-1 font-mono text-xs text-text-faint">
              {result.server_info.name ?? "?"} v{result.server_info.version ?? "?"} · entrypoint:{" "}
              {result.bin_name}
            </div>
            <div className="mt-2 text-sm text-text-muted">
              Declared {result.tools.length} real tool{result.tools.length === 1 ? "" : "s"} — static
              checks only, no tool was actually called (see &ldquo;Why this matters&rdquo; for why).
            </div>
          </div>

          <div className="space-y-2">
            {result.tools.map((tool) => (
              <Link
                key={tool.name}
                href={`/tool/${encodeURIComponent(result.package_name)}/${encodeURIComponent(tool.name)}`}
                className="flex items-center gap-3 rounded-lg border border-border bg-surface px-4 py-3 transition-colors hover:bg-surface-raised"
              >
                <GradeBadge grade={tool.grade} size="sm" />
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-sm text-text">{tool.name}</div>
                  <div className="truncate text-xs text-text-faint">{tool.description}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
