import { cn } from "@/lib/cn";
import type { Confidence } from "@/lib/schema";

const STYLES: Record<Confidence, string> = {
  high: "bg-[var(--confidence-high)]/15 text-[var(--confidence-high)] ring-[var(--confidence-high)]/30",
  medium:
    "bg-[var(--confidence-medium)]/15 text-[var(--confidence-medium)] ring-[var(--confidence-medium)]/30",
  low: "bg-[var(--confidence-low)]/15 text-[var(--confidence-low)] ring-[var(--confidence-low)]/30",
  unmatched:
    "bg-[var(--confidence-unmatched)]/15 text-[var(--confidence-unmatched)] ring-[var(--confidence-unmatched)]/30",
};

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wide ring-1 ring-inset",
        STYLES[confidence],
      )}
    >
      {confidence}
    </span>
  );
}
