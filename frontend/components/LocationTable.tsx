"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import type { ListLocationsResponse } from "@/lib/api-contract";

import { ConfidenceBadge } from "./ConfidenceBadge";

export function LocationTable() {
  const [data, setData] = useState<ListLocationsResponse | null>(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams({ limit: "100", offset: "0" });
    if (search) params.set("search", search);
    fetch(`/api/locations?${params}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [search]);

  if (error) {
    return (
      <div className="app-panel border-[var(--confidence-unmatched)]/40 p-4 text-sm text-[var(--confidence-unmatched)]">
        Failed to load locations: {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="app-panel p-8">
        <div className="flex items-center gap-3 text-sm text-[var(--muted-foreground)]">
          <span className="inline-block h-4 w-4 animate-pulse rounded-full bg-[var(--primary)]/40" />
          Loading locations…
        </div>
      </div>
    );
  }

  const usingFixtures = data.rows.some((r) => r.overture_release === "fixture-1.0");

  return (
    <div className="space-y-4">
      {usingFixtures ? (
        <div className="app-panel border-[var(--primary)]/35 px-4 py-3 text-sm text-[var(--muted-foreground)]">
          <span className="font-medium text-[var(--foreground)]">Offline fixture data.</span> Map
          pins and footprints use synthetic coordinates. Run{" "}
          <code className="rounded bg-[var(--muted)] px-1 font-mono text-xs">make sample</code> for
          live Google geocodes and Overture buildings on satellite imagery.
        </div>
      ) : null}
      <div className="app-panel p-4">
        <label className="flex items-center gap-3 rounded-md border border-[var(--border)] bg-[var(--muted)] px-3 py-2 focus-within:border-[var(--primary)] focus-within:ring-[3px] focus-within:ring-[color-mix(in_srgb,var(--primary)_22%,transparent)]">
          <span className="sr-only">Search locations</span>
          <Search
            className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]"
            strokeWidth={1.75}
            aria-hidden
          />
          <input
            type="search"
            placeholder="Search location id or address…"
            className="min-w-0 flex-1 border-0 bg-transparent text-sm text-[var(--foreground)] outline-none placeholder:text-[var(--muted-foreground)]"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <p className="mt-3 font-mono text-xs text-[var(--muted-foreground)]">
          {data.total.toLocaleString()} locations · showing {data.rows.length}
        </p>
      </div>

      <div className="app-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="app-table min-w-full text-left text-sm">
            <thead>
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Address</th>
                <th className="px-4 py-3 text-right">Sqft</th>
                <th className="px-4 py-3">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.location_id}>
                  <td className="px-4 py-3 font-mono text-xs">
                    <Link
                      className="underline decoration-[var(--border-strong)] underline-offset-2 hover:decoration-[var(--primary)]"
                      href={`/locations/${row.location_id}`}
                    >
                      {row.location_id}
                    </Link>
                  </td>
                  <td className="max-w-md truncate px-4 py-3 text-[var(--muted-foreground)]">
                    {row.address_input}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums font-medium">
                    {row.estimated_sqft?.toLocaleString() ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge confidence={row.confidence} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
