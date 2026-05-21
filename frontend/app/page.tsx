import { LocationTable } from "@/components/LocationTable";
import { SampleIdKey } from "@/components/SampleIdKey";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl p-8">
      <header className="mb-8 flex flex-col gap-6 sm:flex-row sm:items-start">
        <div className="min-w-0 flex-1 sm:max-w-[67%]">
          <h1 className="text-3xl font-bold">FootprintIQ</h1>
          <p className="mt-2 text-sm opacity-70">
            Review pipeline estimates against Esri imagery. Click a row for detail.
          </p>
        </div>
        <SampleIdKey />
      </header>
      <LocationTable />
    </main>
  );
}
