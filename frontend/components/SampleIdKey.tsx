/** Explains location_id prefixes on the sample_addresses.csv QA list. */

const PREFIXES = [
  {
    prefix: "WMART_, AMZN_, TGT_, …",
    label: "Sample stores",
    detail: "Real US chain addresses used to exercise Places + Overture on live runs.",
  },
  {
    prefix: "TEST_",
    label: "Harness edge cases (5 rows)",
    detail:
      "Invalid or fictional inputs only: ###, PO Box, Anytown, Evergreen Terrace, non-US site. Expect geocode or footprint failures.",
  },
] as const;

export function SampleIdKey() {
  return (
    <aside className="app-panel w-full shrink-0 border-amber-500/25 p-4 text-sm lg:max-w-sm">
      <p className="app-section-label mb-2 text-amber-700 dark:text-amber-400">Harness</p>
      <h2 className="font-semibold">Sample ID key</h2>
      <p className="mt-1.5 text-xs leading-relaxed text-[var(--muted-foreground)]">
        20-row{" "}
        <code className="rounded bg-[var(--muted)] px-1 font-mono text-[10px]">
          sample_addresses.csv
        </code>{" "}
        harness, not the full 22K portfolio.
      </p>
      <dl className="mt-4 space-y-3 border-t border-[var(--border)] pt-4">
        {PREFIXES.map((row) => (
          <div key={row.prefix}>
            <dt className="font-mono text-xs font-medium text-amber-900 dark:text-amber-200">
              {row.prefix}
            </dt>
            <dd className="mt-1 text-xs leading-relaxed text-[var(--muted-foreground)]">
              <span className="font-medium text-[var(--foreground)]">{row.label}.</span>{" "}
              {row.detail}
            </dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}
