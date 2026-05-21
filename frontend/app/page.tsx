/**
 * Visualizer — list view. OWNED BY LANE D.
 *
 * Wave 0: placeholder that renders without errors so the dev server boots.
 * Lane D MUST replace with:
 *   - Top: FilterBar (search + confidence pills + state + flag toggles)
 *   - Body: virtualized TanStack table over /api/locations rows
 *   - Click row -> /locations/[id]
 */

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Sqft Estimator — QA Visualizer</h1>
        <p className="mt-2 text-sm opacity-70">
          Wave 0 skeleton. Lane D will implement the filterable list + detail view.
        </p>
      </header>
      <section className="rounded-lg border border-[var(--border)] p-6">
        <h2 className="mb-2 text-lg font-semibold">Status</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm opacity-80">
          <li>Backend pipeline: stubbed</li>
          <li>Frontend: stubbed</li>
          <li>
            Contracts: locked in <code>backend/src/sqft/schema.py</code> +{" "}
            <code>frontend/lib/schema.ts</code>
          </li>
          <li>
            See <code>LANES.md</code> for per-lane implementation briefs
          </li>
        </ul>
      </section>
    </main>
  );
}
