"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { ListLocationsResponse } from "@/lib/api-contract";

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
    return <p className="text-red-600">Failed to load locations: {error}</p>;
  }

  if (!data) {
    return <p className="opacity-70">Loading locations…</p>;
  }

  return (
    <div className="space-y-4">
      <input
        type="search"
        placeholder="Search location id or address…"
        className="w-full rounded border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <p className="text-sm opacity-70">
        {data.total} locations · showing {data.rows.length}
      </p>
      <div className="overflow-x-auto rounded border border-[var(--border)]">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-[var(--border)] bg-black/5">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Address</th>
              <th className="px-3 py-2">Sqft</th>
              <th className="px-3 py-2">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => {
              const isTest = row.location_id.startsWith("TEST_");
              return (
              <tr
                key={row.location_id}
                className={`border-b border-[var(--border)]/60 ${isTest ? "bg-amber-500/5" : ""}`}
              >
                <td className="px-3 py-2 font-mono text-xs">
                  <Link
                    className={isTest ? "text-amber-800 underline dark:text-amber-200" : "underline"}
                    href={`/locations/${row.location_id}`}
                  >
                    {row.location_id}
                  </Link>
                </td>
                <td className="max-w-md truncate px-3 py-2">{row.address_input}</td>
                <td className="px-3 py-2 tabular-nums">
                  {row.estimated_sqft?.toLocaleString() ?? "—"}
                </td>
                <td className="px-3 py-2 capitalize">{row.confidence}</td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
