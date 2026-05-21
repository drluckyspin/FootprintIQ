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
    <dl className="space-y-2 text-sm">
      {items.map(([label, value]) => (
        <div key={label} className="grid grid-cols-2 gap-2">
          <dt className="opacity-70">{label}</dt>
          <dd className="font-mono text-xs">{String(value)}</dd>
        </div>
      ))}
      {detail.flags.length > 0 ? (
        <div className="pt-2">
          <dt className="mb-1 opacity-70">Flags</dt>
          <ul className="list-disc space-y-1 pl-4">
            {detail.flags.map((f) => (
              <li key={f.key}>
                <span className="font-medium">{f.key}</span>: {f.explanation}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </dl>
  );
}
