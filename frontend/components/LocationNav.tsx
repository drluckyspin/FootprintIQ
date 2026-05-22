"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { cn } from "@/lib/cn";

export function LocationNav({
  locationId,
  prevId,
  nextId,
}: {
  locationId: string;
  prevId: string | null;
  nextId: string | null;
}) {
  const router = useRouter();

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" && prevId) router.push(`/locations/${prevId}`);
      if (e.key === "ArrowRight" && nextId) router.push(`/locations/${nextId}`);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prevId, nextId, router]);

  const navBtn =
    "inline-flex items-center gap-1 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-xs transition-colors hover:bg-[var(--muted)] disabled:pointer-events-none disabled:opacity-35";

  return (
    <nav className="flex items-center gap-2 font-mono text-xs" aria-label="Location navigation">
      {prevId ? (
        <Link className={navBtn} href={`/locations/${prevId}`} title={prevId}>
          <ChevronLeft className="h-3.5 w-3.5" strokeWidth={2} />
          <span className="hidden max-w-[8rem] truncate sm:inline">{prevId}</span>
        </Link>
      ) : (
        <span className={cn(navBtn, "opacity-35")} aria-disabled>
          <ChevronLeft className="h-3.5 w-3.5" strokeWidth={2} />
        </span>
      )}
      <span className="rounded-md bg-[var(--muted)] px-2 py-1 font-medium text-[var(--foreground)]">
        {locationId}
      </span>
      {nextId ? (
        <Link className={navBtn} href={`/locations/${nextId}`} title={nextId}>
          <span className="hidden max-w-[8rem] truncate sm:inline">{nextId}</span>
          <ChevronRight className="h-3.5 w-3.5" strokeWidth={2} />
        </Link>
      ) : (
        <span className={cn(navBtn, "opacity-35")} aria-disabled>
          <ChevronRight className="h-3.5 w-3.5" strokeWidth={2} />
        </span>
      )}
      <span className="ml-1 hidden text-[10px] text-[var(--muted-foreground)] lg:inline">
        ← → keys
      </span>
    </nav>
  );
}
