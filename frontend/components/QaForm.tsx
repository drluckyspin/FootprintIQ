"use client";

import { useState } from "react";

import type { EstimateRow } from "@/lib/schema";

export function QaForm({ row }: { row: EstimateRow }) {
  const [status, setStatus] = useState<string | null>(null);
  const [buildingSelection, setBuildingSelection] = useState("correct");
  const [sqftAssessment, setSqftAssessment] = useState("unknown");
  const [notes, setNotes] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("Saving…");
    const res = await fetch("/api/qa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        location_id: row.location_id,
        pipeline_run_id: row.pipeline_run_id,
        reviewer: "local",
        building_selection: buildingSelection,
        sqft_assessment: sqftAssessment,
        notes: notes || null,
      }),
    });
    if (!res.ok) {
      setStatus("Failed to save QA review");
      return;
    }
    setStatus("Saved");
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded border border-[var(--border)] p-4">
      <h3 className="font-semibold">QA review</h3>
      <label className="block text-sm">
        Building selection
        <select
          className="mt-1 w-full rounded border border-[var(--border)] bg-transparent px-2 py-1"
          value={buildingSelection}
          onChange={(e) => setBuildingSelection(e.target.value)}
        >
          <option value="correct">correct</option>
          <option value="wrong">wrong</option>
          <option value="ambiguous">ambiguous</option>
        </select>
      </label>
      <label className="block text-sm">
        Sqft assessment
        <select
          className="mt-1 w-full rounded border border-[var(--border)] bg-transparent px-2 py-1"
          value={sqftAssessment}
          onChange={(e) => setSqftAssessment(e.target.value)}
        >
          <option value="unknown">unknown</option>
          <option value="low">low</option>
          <option value="right">right</option>
          <option value="high">high</option>
        </select>
      </label>
      <label className="block text-sm">
        Notes
        <textarea
          className="mt-1 w-full rounded border border-[var(--border)] bg-transparent px-2 py-1"
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>
      <button
        type="submit"
        className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
      >
        Submit review
      </button>
      {status ? <p className="text-sm opacity-80">{status}</p> : null}
    </form>
  );
}
