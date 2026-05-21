# roof-survey — Building Square Footage Estimator

Pipeline for estimating building square footage at ~22K US retail and warehouse locations
by geocoding addresses, joining to Overture Maps building footprints, and computing area
in EPSG:5070 (CONUS Albers Equal Area). Ships with a Next.js + MapLibre visualizer for
human QA.

## Quick start

```bash
make check          # verify toolchain + .env files
make install        # uv sync (backend) + bun install (frontend)
make fixtures       # regenerate deterministic test parquet files
make test-smoke     # confirm contracts + fixtures intact
make viz            # start visualizer dev server at http://localhost:3000
```

End-to-end run (after Wave 1 lanes ship their implementations):

```bash
make sample         # run on the 20-row fixture CSV
make full           # run on data/input/all.csv with --max-cost-usd 250
make report         # generate data/output/report.html
make viz            # browse results in the visualizer
```

## Project shape

```
backend/      Python + uv. Pipeline (normalize, geocode, overture, spatial_join, area, floors, flags).
frontend/     Next.js + Bun + Tailwind + shadcn + MapLibre. Per-address visualizer + QA form.
data/         Gitignored. data/input/ raw CSVs (PII), data/interim/, data/output/.
tests/        Cross-stack: fixtures/, shared test data.
LANES.md      Per-lane briefs for the 4 Wave 1 agents.
ROOF_PROJECT_PLAN.md   Original (superseded) plan.
roof-sqft-revised-plan_*.plan.md   Current plan.
```

## Working model

Built so multiple AI agents can implement in parallel. See `LANES.md` for per-lane
contracts and file ownership.

| Stage | Agents | Wall time |
|---|---|---|
| Wave 0 (foundation) | 1 serial | ~1 day (done) |
| Wave 1 (lanes A, B, C, D) | 4 parallel | ~1.5 days |
| Wave 2 (integration) | 1 | ~1 day |
| Wave 3 (ground truth + full run) | 1 | ~1 day |

## License

Internal — Bain Innovation Accelerator.
