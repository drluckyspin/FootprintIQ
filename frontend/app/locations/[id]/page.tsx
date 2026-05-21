/**
 * Visualizer — detail view. OWNED BY LANE D.
 *
 * Wave 0: placeholder.
 * Lane D MUST replace with:
 *   - Left ~65%: react-map-gl/MapLibre with Esri World Imagery basemap
 *       layers: geocoded point, chosen polygon, candidate polygons (faded),
 *       search buffer circle, optional parcel outline
 *   - Right ~35%: calc trace card + QA form
 *   - Keyboard: left/right to navigate prev/next location in current filter
 */

import { notFound } from "next/navigation";

interface DetailPageProps {
  params: { id: string };
}

export default async function LocationDetailPage({ params }: DetailPageProps) {
  if (!params.id) notFound();
  return (
    <main className="mx-auto max-w-6xl p-8">
      <h1 className="text-2xl font-bold">Location: {params.id}</h1>
      <p className="mt-2 text-sm opacity-70">
        Wave 0 stub. Lane D will render the MapLibre map + calc trace + QA form here.
      </p>
    </main>
  );
}
