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
    <form onSubmit={submit} className="app-panel space-y-4 p-5">
      <div>
        <p className="app-section-label mb-1">Human review</p>
        <h3 className="text-sm font-semibold">QA review</h3>
      </div>
      <label className="block text-sm">
        <span className="mb-1.5 block text-[var(--muted-foreground)]">Building selection</span>
        <select
          className="app-input"
          value={buildingSelection}
          onChange={(e) => setBuildingSelection(e.target.value)}
        >
          <option value="correct">correct</option>
          <option value="wrong">wrong</option>
          <option value="ambiguous">ambiguous</option>
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1.5 block text-[var(--muted-foreground)]">Sqft assessment</span>
        <select
          className="app-input"
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
        <span className="mb-1.5 block text-[var(--muted-foreground)]">Notes</span>
        <textarea
          className="app-input min-h-[88px] resize-y"
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>
      <div className="flex flex-wrap items-center gap-3 pt-1">
        <button type="submit" className="app-btn-primary">
          Submit review
        </button>
        {status ? (
          <p className="font-mono text-xs text-[var(--muted-foreground)]">{status}</p>
        ) : null}
      </div>
    </form>
  );
}
