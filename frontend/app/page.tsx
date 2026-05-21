import { LocationTable } from "@/components/LocationTable";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Sqft Estimator — QA Visualizer</h1>
        <p className="mt-2 text-sm opacity-70">
          Review pipeline estimates against Esri imagery. Click a row for detail.
        </p>
      </header>
      <LocationTable />
    </main>
  );
}
