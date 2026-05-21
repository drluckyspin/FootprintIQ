/** Explains location_id prefixes on the sample_addresses.csv QA list. */

const PREFIXES = [
  {
    prefix: "WMART_, AMZN_, TGT_, …",
    label: "Sample stores",
    detail: "Real US chain addresses used to exercise Places + Overture on live runs.",
  },
  {
    prefix: "TEST_",
    label: "Test-only rows",
    detail:
      "Fictional or invalid addresses (Anytown, Evergreen Terrace, PO Box, etc.). Expect geocode or match failures — not production data.",
  },
] as const;

export function SampleIdKey() {
  return (
    <aside className="w-full shrink-0 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm sm:ml-auto sm:w-1/3 sm:max-w-[33%]">
      <h2 className="font-semibold text-amber-950 dark:text-amber-100">Sample ID key</h2>
      <p className="mt-1 text-xs opacity-80">
        This list is the 20-row <code className="font-mono">sample_addresses.csv</code> harness,
        not the full 22K portfolio.
      </p>
      <dl className="mt-3 space-y-3">
        {PREFIXES.map((row) => (
          <div key={row.prefix}>
            <dt className="font-mono text-xs font-medium text-amber-900 dark:text-amber-200">
              {row.prefix}
            </dt>
            <dd className="mt-0.5 text-xs opacity-90">
              <span className="font-medium">{row.label}.</span> {row.detail}
            </dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}
