/**
 * The rule-based + AI engine two-column verdict, used everywhere a scan
 * result gets shown (live scan result, tool detail page). One shared
 * component so the two views can't quietly drift apart, the same
 * reasoning that keeps the CLI and API calling one engine.run_scan().
 */
export type EngineResultPanelProps = {
  ruleScore: number;
  ruleFlags: string[];
  llmRiskLevel: string | null;
  llmFlaggedPhrases: string[];
  llmReasoning: string | null;
  llmError?: string | null;
};

export function EngineResultPanel({
  ruleScore,
  ruleFlags,
  llmRiskLevel,
  llmFlaggedPhrases,
  llmReasoning,
  llmError,
}: EngineResultPanelProps) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <div>
        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-text-faint">Rule-based engine</h3>
        <div className="mb-2 font-mono text-sm text-text-muted">Risk score: {ruleScore}/100</div>
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
      </div>

      <div>
        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-text-faint">AI engine (semantic)</h3>
        {llmError ? (
          <div className="text-sm text-grade-f">{llmError}</div>
        ) : (
          <>
            <div className="mb-2 font-mono text-sm text-text-muted">Risk level: {llmRiskLevel ?? "—"}</div>
            {llmFlaggedPhrases.length > 0 && (
              <ul className="mb-2 space-y-1.5">
                {llmFlaggedPhrases.map((p, i) => (
                  <li key={i} className="rounded bg-grade-f-soft px-2 py-1 font-mono text-xs text-grade-f">
                    &ldquo;{p}&rdquo;
                  </li>
                ))}
              </ul>
            )}
            {llmReasoning && <p className="text-sm text-text-muted">{llmReasoning}</p>}
          </>
        )}
      </div>
    </div>
  );
}
