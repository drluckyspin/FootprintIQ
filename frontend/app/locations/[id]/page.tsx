import Link from "next/link";
import { notFound } from "next/navigation";

import { CalcTrace } from "@/components/CalcTrace";
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

  return (
    <main className="mx-auto max-w-6xl p-8">
      <div className="mb-4 flex items-center justify-between gap-4">
        <Link href="/" className="text-sm underline">
          ← All locations
        </Link>
        <LocationNav locationId={params.id} prevId={prevId} nextId={nextId} />
      </div>
      <header className="mb-6">
        <h1 className="text-2xl font-bold">{detail.row.location_id}</h1>
        <p className="mt-1 text-sm opacity-80">{detail.row.address_input}</p>
      </header>
      <div className="grid gap-6 lg:grid-cols-2">
        <LocationMap detail={detail} />
        <div className="space-y-6">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Calculation trace</h2>
            <CalcTrace detail={detail} />
          </section>
          <QaForm row={detail.row} />
        </div>
      </div>
    </main>
  );
}
