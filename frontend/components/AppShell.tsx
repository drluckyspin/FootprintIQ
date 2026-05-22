"use client";

import Link from "next/link";

import { ThemeToggle } from "./ThemeToggle";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen">
      <div className="app-bg" aria-hidden="true">
        <div className="app-bg-orb app-bg-orb-1" />
        <div className="app-bg-orb app-bg-orb-2" />
        <div className="app-bg-grid" />
      </div>

      <header className="app-nav sticky top-0 z-50">
        <div className="mx-auto flex h-[4.25rem] max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link
            href="/"
            className="truncate text-2xl font-bold tracking-tight text-[var(--foreground)] sm:text-3xl"
          >
            FootprintIQ
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden font-mono text-[10px] uppercase tracking-wider text-[var(--muted-foreground)] md:inline">
              Pipeline review
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="relative z-10">{children}</div>
    </div>
  );
}
