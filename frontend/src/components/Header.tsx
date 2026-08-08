"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeToggle";

const LINKS = [
  { href: "/registry", label: "Registry" },
  { href: "/story", label: "Why this matters" },
];

export function Header() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Close the mobile menu on navigation. Deliberately done during render
  // (React's documented pattern for "reset state when a prop changes"),
  // not in a useEffect - this needs to happen before the browser paints
  // the new page with the old menu still open, not one render later.
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setOpen(false);
  }

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-4 sm:px-6">
        <Link href="/" className="flex min-w-0 items-center gap-2.5" onClick={() => setOpen(false)}>
          <span className="flex h-7 w-7 flex-none items-center justify-center rounded-md bg-accent text-accent-contrast">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M12 2 3 6v6c0 5 3.8 8.7 9 10 5.2-1.3 9-5 9-10V6l-9-4Z" />
              <path d="m8.5 12 2.3 2.3L16 9" />
            </svg>
          </span>
          <span className="truncate font-semibold tracking-tight">MCP Trust Registry</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 sm:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded-lg px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text hover:bg-surface-raised"
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/scan"
            className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-accent-contrast transition-opacity hover:opacity-90"
          >
            Scan a tool
          </Link>
          <div className="ml-2">
            <ThemeToggle />
          </div>
        </nav>

        {/* Mobile controls */}
        <div className="flex flex-none items-center gap-2 sm:hidden">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-text-muted transition-colors hover:text-text hover:border-text-faint"
          >
            {open ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu panel - normal document flow, not overlaid, so the
          sticky header just grows and pushes the page down while open. */}
      {open && (
        <nav data-testid="mobile-nav" className="flex flex-col gap-1 border-t border-border px-4 py-3 sm:hidden">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="rounded-lg px-3 py-2.5 text-sm text-text-muted transition-colors hover:bg-surface-raised hover:text-text"
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/scan"
            onClick={() => setOpen(false)}
            className="mt-1 rounded-lg bg-accent px-3 py-2.5 text-center text-sm font-medium text-accent-contrast"
          >
            Scan a tool
          </Link>
        </nav>
      )}
    </header>
  );
}
