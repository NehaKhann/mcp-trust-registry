"use client";

import { useState } from "react";
import { PasteScan } from "@/components/PasteScan";
import { LivePackageScan } from "@/components/LivePackageScan";

export default function ScanPage() {
  const [mode, setMode] = useState<"paste" | "live">("paste");

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Scan a tool before you install it</h1>
        <p className="mt-1 text-text-muted">
          Found a new MCP server on GitHub or npm? Paste its declared tools here first —{" "}
          <b className="text-text">before</b> you <code className="font-mono text-xs">git clone</code> the repo or
          run <code className="font-mono text-xs">npm install</code> — and get a graded verdict, live, checked
          against a rule engine and a local model, saved to the registry.
        </p>
      </div>

      <div className="mb-8 flex gap-1 border-b border-border">
        <TabButton active={mode === "paste"} onClick={() => setMode("paste")}>
          Paste a description
        </TabButton>
        <TabButton active={mode === "live"} onClick={() => setMode("live")}>
          Scan a live npm package
        </TabButton>
      </div>

      {mode === "paste" && <PasteScan />}
      {mode === "live" && <LivePackageScan />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`-mb-px border-b-2 px-3 py-2.5 text-sm font-medium transition-colors ${
        active ? "border-accent text-text" : "border-transparent text-text-muted hover:text-text"
      }`}
    >
      {children}
    </button>
  );
}
