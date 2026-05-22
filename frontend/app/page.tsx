import { LocationTable } from "@/components/LocationTable";
import { SampleIdKey } from "@/components/SampleIdKey";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="mb-8 flex flex-col gap-6 lg:flex-row lg:items-start">
        <div className="min-w-0 flex-1">
          <p className="app-section-label mb-2">Portfolio review</p>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Analysis Results</h1>
          <div className="mt-2 max-w-2xl space-y-3 text-sm leading-relaxed text-[var(--muted-foreground)]">
            <p className="text-base font-light text-[var(--foreground)]">
              Click on a location to see satellite imagery, the AI-derived building polygon, how the
              number was calculated, and optionally record whether the match and sqft look right.
            </p>
            <p>
              The backend pipeline geocodes each store or warehouse address, pulls the matching
              building footprint from Overture Maps, estimates total square footage from footprint
              area and floor count, and writes one auditable row per location.
            </p>
          </div>
        </div>
        <SampleIdKey />
      </header>
      <LocationTable />
    </main>
  );
}
