"use client";

import { Moon, Sun } from "lucide-react";

import { cn } from "@/lib/cn";
import { useTheme } from "./ThemeProvider";

export function ThemeToggle({ className }: { className?: string }) {
  const { toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        "inline-flex h-9 w-9 items-center justify-center rounded-md border transition-colors",
        "border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]",
        "hover:border-[var(--border-strong)] hover:bg-[var(--muted)]",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)]",
        className,
      )}
      aria-label="Toggle color theme"
      title="Toggle color theme"
    >
      {/* Both icons always in DOM — visibility via [data-theme] in globals.css (avoids hydration mismatch). */}
      <Sun
        className="theme-toggle-icon theme-toggle-icon-sun h-4 w-4"
        strokeWidth={1.75}
        aria-hidden
      />
      <Moon
        className="theme-toggle-icon theme-toggle-icon-moon h-4 w-4"
        strokeWidth={1.75}
        aria-hidden
      />
    </button>
  );
}
