import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import Link from "next/link";
import "./globals.css";
import { ThemeToggle, THEME_INIT_SCRIPT } from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "MCP Trust Registry",
  description: "Runtime + semantic trust registry for MCP servers — catches tool poisoning and scope creep before you connect to it.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-screen">
        <header className="sticky top-0 z-10 border-b border-border bg-bg/80 backdrop-blur">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-accent-contrast">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M12 2 3 6v6c0 5 3.8 8.7 9 10 5.2-1.3 9-5 9-10V6l-9-4Z" />
                  <path d="m8.5 12 2.3 2.3L16 9" />
                </svg>
              </span>
              <span className="font-semibold tracking-tight">MCP Trust Registry</span>
            </Link>
            <nav className="flex items-center gap-1">
              <Link
                href="/"
                className="rounded-lg px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text hover:bg-surface-raised"
              >
                Registry
              </Link>
              <Link
                href="/story"
                className="rounded-lg px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text hover:bg-surface-raised"
              >
                Why this matters
              </Link>
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
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
