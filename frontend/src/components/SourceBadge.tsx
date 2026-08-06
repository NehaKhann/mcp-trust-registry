import type { ScanSource } from "@/lib/api";

export function SourceBadge({ source }: { source: ScanSource }) {
  if (source === "docker-sandbox") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-accent/30 bg-accent-soft px-2 py-0.5 text-xs font-medium text-accent">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 6 9 17l-5-5" />
        </svg>
        Verified in sandbox
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-raised px-2 py-0.5 text-xs text-text-muted">
      Static only
    </span>
  );
}
