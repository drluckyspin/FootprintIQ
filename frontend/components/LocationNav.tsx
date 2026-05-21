"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

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

  return (
    <nav className="flex items-center gap-3 text-sm">
      {prevId ? (
        <Link className="underline" href={`/locations/${prevId}`}>
          ← {prevId}
        </Link>
      ) : (
        <span className="opacity-40">←</span>
      )}
      <span className="font-mono">{locationId}</span>
      {nextId ? (
        <Link className="underline" href={`/locations/${nextId}`}>
          {nextId} →
        </Link>
      ) : (
        <span className="opacity-40">→</span>
      )}
    </nav>
  );
}
