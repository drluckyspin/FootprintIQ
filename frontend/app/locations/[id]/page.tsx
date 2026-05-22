import Link from "next/link";
import { notFound } from "next/navigation";

import { CalcTrace } from "@/components/CalcTrace";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { LocationMap } from "@/components/LocationMap";
import { LocationNav } from "@/components/LocationNav";
import { QaForm } from "@/components/QaForm";
import { getLocationDetail, listLocations } from "@/lib/queries";

export default async function LocationDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const detail = await getLocationDetail(params.id);
  if (!detail) notFound();

  const list = await listLocations({ limit: 1000, offset: 0 });
  const ids = list.rows.map((r) => r.location_id).sort();
  const idx = ids.indexOf(params.id);
  const prevId = idx > 0 ? ids[idx - 1] : null;
  const nextId = idx >= 0 && idx < ids.length - 1 ? ids[idx + 1] : null;
  const { row } = detail;

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Link href="/" className="app-link text-sm">
          ← All locations
        </Link>
        <LocationNav locationId={params.id} prevId={prevId} nextId={nextId} />
      </div>

      <header className="app-panel mb-6 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="app-section-label mb-2">Location</p>
            <h1 className="font-mono text-xl font-bold tracking-tight sm:text-2xl">
              {row.location_id}
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-[var(--muted-foreground)]">
              {row.address_input}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <ConfidenceBadge confidence={row.confidence} />
            {row.estimated_sqft != null ? (
              <div className="text-right">
                <p className="font-mono text-[10px] uppercase tracking-wider text-[var(--muted-foreground)]">
                  Estimated
                </p>
                <p className="tabular-nums text-2xl font-semibold">
                  {row.estimated_sqft.toLocaleString()}
                  <span className="ml-1 text-sm font-normal text-[var(--muted-foreground)]">
                    sqft
                  </span>
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <div className="mb-3 flex items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold">Satellite + footprint</h2>
            <span className="font-mono text-[10px] text-[var(--muted-foreground)]">
              Esri imagery
            </span>
          </div>
          <LocationMap detail={detail} />
        </section>
        <div className="space-y-6">
          <section className="app-panel p-5">
            <p className="app-section-label mb-3">Trace</p>
            <h2 className="mb-4 text-sm font-semibold">Calculation trace</h2>
            <CalcTrace detail={detail} />
          </section>
          <QaForm row={detail.row} />
        </div>
      </div>
    </main>
  );
}
