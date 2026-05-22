# Wave 1 Lane Briefs

This file is the canonical prompt source for every Wave 1 lane agent. Each lane runs
in its own `git worktree` on its own branch, reads only the contracts + fixtures
locked by Wave 0, and edits **only** the files in its allowlist below.

## Common rules (apply to every lane)

- **Branch**: `wave1/<lane-id>` (e.g. `wave1/lane-a-ingest`).
- **Worktree**: `git worktree add ../footprintiq-<lane-id> wave1/<lane-id>`.
- **Frozen contracts** — do not edit:
  - `backend/src/sqft/schema.py`
  - `frontend/lib/schema.ts`
  - `frontend/lib/api-contract.ts`
  - `backend/src/sqft/io.py` (the column-list constants + `expected_columns`)
  - `tests/fixtures/**` (regenerate only via `make fixtures` and only with orchestrator approval)
- **Frozen tooling** — do not edit unless adding a dep the orchestrator approved:
  - `Makefile`, `Common.make`, `backend/pyproject.toml`, `frontend/package.json`,
    `.github/workflows/*`, `.pre-commit-config.yaml`.
- **No new dependencies** in your lane without an orchestrator-approved sub-PR to `pyproject.toml` / `package.json`.
- Every PR must pass `make check` (env+deps) + `make test-lane-<x>` + `make test-smoke` + `make typecheck`.
- If you discover the contract is wrong/insufficient → **stop**, leave a note in `LANE_<X>_NOTES.md`, and escalate. Do not silently change the schema.
- Don't touch any file outside your allowlist. If you need a helper that's in shared code, propose it via PR comment.
- Keep your PR scoped to your lane. Don't add adjacent improvements.

---

## Lane A — Address ingestion

**Goal**: Take raw address rows in, produce a deterministic geocoded parquet out, with cached HTTP and chain-aware provider routing.

**Files you own (allowlist):**
- `backend/src/sqft/normalize.py`
- `backend/src/sqft/dedup.py`
- `backend/src/sqft/geocode.py`
- `backend/src/sqft/places.py`
- `backend/tests/test_lane_a.py` (and split it into multiple files if helpful, all under tests/)
- New test helpers under `backend/tests/_helpers_lane_a/` if needed

**Contracts you consume:**
- `schema.RawAddress` (input rows)
- `schema.GeocoderPrecision`, `schema.GeocoderProvider` (enums)
- `config.GeocoderConfig` (chain_tokens, rate limits, cache path)
- `io.write_parquet(rows, path, "normalized" | "geocoded")` for output

**Contracts you produce:**
- `schema.NormalizedAddress` rows -> `data/interim/normalized.parquet`
- `schema.GeocodeResult` rows -> `data/interim/geocoded.parquet`

**Tests that must pass:**
- `make test-lane-a` — flip `pytestmark` in `test_lane_a.py` from `skip` to `lane_a`.
- `make test-smoke` — must remain green.
- `make typecheck` — must remain green.

**Definition of done:**
- [ ] `normalize_addresses(read sample_addresses.csv)` produces rows that byte-identical to `tests/fixtures/normalized.parquet` (modulo row order if you choose deterministic sort).
- [ ] `geocode_batch` with `respx`-mocked Places + Geocoding produces rows matching `tests/fixtures/geocoded.parquet`.
- [ ] Second call to `geocode_batch` with the same input produces zero HTTP requests (cache hit).
- [ ] `estimate_cost_usd` returns a `dict` with `total_usd` and the breakdown keys documented in the docstring.
- [ ] Addresses containing a `chain_token` route through Places; others route through Geocoding.

**Escalation triggers:**
- If real Google Places response shape doesn't fit `GeocodeResult` — escalate before changing the schema.
- If `usaddress` cannot parse one of the deliberately-broken fixture rows in a way that's stable — escalate.

---

## Lane B — Spatial

**Goal**: Pull Overture footprints for a bbox, decide which building each point belongs to, compute area in EPSG:5070, resolve floors with subtype awareness, and evaluate flags.

**Files you own (allowlist):**
- `backend/src/sqft/overture.py`
- `backend/src/sqft/parcels.py` (interface only — `ParcelProvider` Protocol + `NullParcelProvider`)
- `backend/src/sqft/spatial_join.py`
- `backend/src/sqft/area.py`
- `backend/src/sqft/floors.py`
- `backend/src/sqft/flags.py`
- `backend/tests/test_lane_b.py` + new helpers under `backend/tests/_helpers_lane_b/`

**Contracts you consume:**
- `schema.GeocodeResult` (from `tests/fixtures/geocoded.parquet` — do NOT depend on Lane A's actual code path)
- `schema.Footprint`
- `config.OvertureConfig`, `config.SpatialConfig`, `config.FloorsConfig`

**Contracts you produce:**
- `schema.Footprint` rows -> `data/interim/footprints.parquet`
- `schema.BuildingMatch` rows (in-memory; consumed by Lane C)
- Sets these EstimateRow fields: `building_id, match_method, multi_building_count, candidates_json, footprint_area_sqft, num_floors_used, floors_source, raw_overture_height, raw_overture_num_floors, estimated_sqft, overture_class, overture_subtype, overture_source, overture_update_time, confidence, flags_json, flag_*`.

**Tests that must pass:**
- `make test-lane-b`, `make test-smoke`, `make typecheck`.
- `polygon_area_sqft` matches every entry in `tests/fixtures/expected_areas.json` within its tolerance.

**Definition of done:**
- [ ] Querying real Overture via `fetch_footprints` for the bbox of `geocoded.parquet` returns at most a few thousand polygons (NOT millions) — proving bbox push-down works.
- [ ] A `warehouse` subtype with `height=12` returns 1 floor, never 3.
- [ ] `evaluate_flags(row)` produces a `flags_json` JSON array consistent with the boolean columns (same set of flags, stable ordering by `FlagKey`).
- [ ] `resolve_confidence` returns the right tier per the plan.

**Escalation triggers:**
- If Overture's latest release returns a column not in our `Footprint` schema (e.g. a new attribute we want).
- If `class`/`subtype` values from Overture don't align with our `DEFAULT_FLOORS_BY_SUBTYPE` keys.

---

## Lane C — Pipeline + manifest + validate + io + config

**Goal**: Wire stages together with resume logic, write a full reproducibility manifest, expose a typer CLI, and generate the HTML report + stratified QA worksheet.

**Files you own (allowlist):**
- `backend/src/sqft/manifest.py`
- `backend/src/sqft/pipeline.py`
- `backend/src/sqft/cli.py`
- `backend/src/sqft/validate.py`
- `backend/src/sqft/config.py` (the `load_settings` body only — keep field shapes locked)
- `backend/src/sqft/io.py` (`read_input_csv` body only — DO NOT change `expected_columns` or `_COLS_BY_KIND`)
- `config.yaml`
- `backend/tests/test_lane_c.py`

**Contracts you consume:**
- All `schema.*` types
- Lane A and Lane B function signatures (you may import their modules, but for tests you read from `tests/fixtures/*.parquet` rather than running their code)

**Contracts you produce:**
- `data/output/estimates.parquet` (full `schema.EstimateRow` schema)
- `data/output/run_<id>/manifest.json` (validates against `schema.RunManifest`)
- `data/output/report.html`
- `data/output/qa_worksheet.csv`

**Tests that must pass:**
- `make test-lane-c`, `make test-smoke`, `make typecheck`.
- `make sample` runs end-to-end on a small fixture-derived CSV.

**Definition of done:**
- [ ] `pipeline.run(fixture_csv, settings)` produces an `estimates.parquet` that matches `tests/fixtures/estimates.parquet` on all geometry-derived columns.
- [ ] Re-running with `resume=True` does not redo completed stages (assertable via stage_durations_seconds for skipped stages).
- [ ] Manifest JSON round-trips through `RunManifest.model_validate_json` without errors.
- [ ] `generate_qa_worksheet(..., seed=0)` is deterministic.

**Escalation triggers:**
- If you need an EstimateRow field not in the schema — escalate.
- If `--max-cost-usd` semantics need to change — escalate.

---

## Lane D — Frontend visualizer

**Goal**: Next.js + MapLibre visualizer reading pipeline parquet directly via `@duckdb/node-api`. List view + detail view + QA form.

**Files you own (allowlist):**
- `frontend/lib/duckdb.ts`
- `frontend/lib/queries.ts`
- `frontend/app/api/locations/route.ts`
- `frontend/app/api/locations/[id]/route.ts`
- `frontend/app/api/qa/route.ts`
- `frontend/app/api/runs/route.ts`
- `frontend/app/page.tsx`
- `frontend/app/locations/[id]/page.tsx`
- `frontend/components/**` (create as needed)
- `frontend/tests/**` (Vitest)

**MUST NOT TOUCH**:
- `frontend/lib/schema.ts`, `frontend/lib/api-contract.ts` (Wave 0 frozen).

**Optional split (orchestrator decides):**
- **D1**: `lib/`, `app/api/`. Develops against fixtures via DuckDB.
- **D2**: `app/page.tsx`, `app/locations/**`, `components/**`. Mocks D1's API contracts with `vi.fn()` until D1 lands.

**Contracts you consume:**
- `lib/schema.ts` (zod schemas)
- `lib/api-contract.ts` (request/response types)
- `tests/fixtures/estimates.parquet`, `footprints.parquet` for local DuckDB queries

**Contracts you produce:**
- The four JSON endpoints listed in `api-contract.ts`
- `data/output/qa_reviews.parquet` (append-only, matches `schema.QaReview`)

**Tests that must pass:**
- `make test-lane-d` (Vitest) + `make typecheck` (tsc --noEmit).
- A Playwright/Vitest test that hits `/api/locations` and `/api/locations/WMART_001` against fixture data.

**Definition of done:**
- [ ] List view renders ≥20 fixture rows; clicking a row navigates to `/locations/[id]`.
- [ ] Detail view shows: MapLibre map with the chosen polygon highlighted + candidate polygons faded + geocoded point + buffer circle; right panel shows the full calc trace; QA form posts to `/api/qa` and appends a row to `qa_reviews.parquet`.
- [ ] `←`/`→` keyboard nav between current-filter rows.
- [ ] `tsc --noEmit` clean.
- [ ] `biome check` clean.

**Escalation triggers:**
- If `@duckdb/node-api` can't read the parquet schema cleanly (e.g. WKB decoding) — escalate.
- If any UI design decision feels heavier than "obvious shadcn defaults" — escalate first.
