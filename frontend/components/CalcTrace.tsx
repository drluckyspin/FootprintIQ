import type { LocationDetailResponse } from "@/lib/api-contract";

export function CalcTrace({ detail }: { detail: LocationDetailResponse }) {
  const { row } = detail;
  const items = [
    ["Match method", row.match_method],
    ["Footprint area (sqft)", row.footprint_area_sqft?.toLocaleString() ?? "—"],
    ["Floors used", row.num_floors_used ?? "—"],
    ["Floors source", row.floors_source ?? "—"],
    ["Estimated sqft", row.estimated_sqft?.toLocaleString() ?? "—"],
    ["Building id", row.building_id ?? "—"],
    ["Multi-building count", row.multi_building_count],
    ["Overture release", row.overture_release ?? "—"],
  ];

  return (
    <dl className="divide-y divide-[var(--border)] text-sm">
      {items.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] gap-3 py-2.5">
          <dt className="text-[var(--muted-foreground)]">{label}</dt>
          <dd className="truncate font-mono text-xs tabular-nums">{String(value)}</dd>
        </div>
      ))}
      {detail.flags.length > 0 ? (
        <div className="py-3">
          <dt className="mb-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
            Flags
          </dt>
          <ul className="space-y-2">
            {detail.flags.map((f) => (
              <li
                key={f.key}
                className="rounded-md border border-[var(--border)] bg-[var(--muted)] px-3 py-2 text-xs"
              >
                <span className="font-mono font-medium text-[var(--primary)]">{f.key}</span>
                <span className="mt-0.5 block text-[var(--muted-foreground)]">{f.explanation}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </dl>
  );
}
