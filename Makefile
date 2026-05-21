# -----------------------------------------------------------------------------------------------------------
# Project Makefile
# Version: 1.11
# Source: https://github.com/Bain/code-red-base/blob/main/Makefile
# -----------------------------------------------------------------------------------------------------------
# This Makefile includes Common.make which provides all the standard Code Red project targets.
#
# To include Common.make in your own Makefile:
#
#   1. Copy Common.make to your project root (or reference it from a shared location)
#   2. Add this line to your Makefile:
#
#      include Common.make
#
#   3. All targets from Common.make will be available. You can:
#      - Override any target by redefining it in your Makefile
#      - Add project-specific targets
#      - Extend existing targets using dependencies
#
# Example:
#   # Include common targets
#   include Common.make
#
#   # Add project-specific target
#   .PHONY: deploy
#   deploy:
#       echo "Deploying project..."
#
#   # Override or extend existing target
#   build: Common.make
#       @echo "Building project-specific components..."
#       $(MAKE) -f Common.make build
#
# -----------------------------------------------------------------------------------------------------------

# Include Common.make - this makes all its targets available
include Common.make

# -----------------------------------------------------------------------------------------------------------
# Project-specific targets — sqft estimator pipeline + visualizer
# -----------------------------------------------------------------------------------------------------------

.PHONY: install ## Install backend (uv sync) + frontend (bun install) dependencies
install: check_uv check_bun
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Installing backend deps (uv sync)"
	@cd backend && uv sync
	@$(LOGGER) log_info "Installing frontend deps (bun install)"
	@cd frontend && bun install

.PHONY: fixtures ## Rebuild deterministic test fixtures (parquet files)
fixtures: check_uv
	@$(LOGGER) log_info "Rebuilding fixtures"
	@cd backend && uv run python ../tests/fixtures/build_fixtures.py

.PHONY: test-lane-a ## Run Lane A tests (address ingestion)
test-lane-a: check_uv
	@cd backend && uv run pytest -m lane_a

.PHONY: test-lane-b ## Run Lane B tests (spatial)
test-lane-b: check_uv
	@cd backend && uv run pytest -m lane_b

.PHONY: test-lane-c ## Run Lane C tests (pipeline)
test-lane-c: check_uv
	@cd backend && uv run pytest -m lane_c

.PHONY: test-lane-d ## Run Lane D tests (frontend)
test-lane-d: check_bun
	@cd frontend && bun run test

.PHONY: test-smoke ## Run Wave 0 smoke tests (contracts + fixtures present)
test-smoke: check_uv
	@cd backend && uv run pytest -m smoke

.PHONY: typecheck ## Run mypy on backend + tsc --noEmit on frontend
typecheck: check_uv check_bun
	@$(LOGGER) log_info "mypy backend"
	@cd backend && uv run mypy src/sqft || true
	@$(LOGGER) log_info "tsc --noEmit frontend"
	@cd frontend && bunx tsc --noEmit

.PHONY: demo ## Run pipeline on sample_addresses.csv using fixture parquets (no API keys)
demo: check_uv
	@$(LOGGER) log_info "Running pipeline on sample_addresses.csv using fixture parquets (no API keys)"
	@bash -ec 'source scripts/loadenv.bash && load_root_env && cd backend && SQFT_USE_FIXTURES=1 uv run python -m sqft.cli run-all ../tests/fixtures/sample_addresses.csv --fixtures'

.PHONY: stac-cache ## Build Overture building parquet index (one-time; cached under data/interim/)
stac-cache: check_uv
	@$(LOGGER) log_info "Building Overture STAC/S3 building file index (cached for make sample)"
	@bash -ec 'source scripts/loadenv.bash && load_root_env && cd backend && uv run python -m sqft.cli stac-cache'

.PHONY: sample ## Live pipeline on sample_addresses.csv (Google + Overture; re-runs all stages)
sample: check_uv stac-cache
	@$(LOGGER) log_info "Live sample run (--no-resume; uses GOOGLE_* keys from .env)"
	@bash -ec 'source scripts/loadenv.bash && load_root_env && cd backend && uv run python -m sqft.cli run-all ../tests/fixtures/sample_addresses.csv --sample-size 500 --no-resume'

.PHONY: full ## Run pipeline on the full 22K (requires --max-cost-usd confirmation)
full: check_uv
	@$(LOGGER) log_warning "About to run on full 22K input — make sure data/input/all.csv exists"
	@bash -ec 'source scripts/loadenv.bash && load_root_env && cd backend && uv run python -m sqft.cli run-all ../data/input/all.csv --max-cost-usd 250'

.PHONY: viz ## Start the visualizer frontend dev server (http://localhost:3000)
viz: check_bun
	@bash -ec 'source scripts/loadenv.bash && load_root_env && cd frontend && echo "SQFT_LOG_LEVEL=$$SQFT_LOG_LEVEL" && bun run dev'

.PHONY: report ## Render data/output/report.html from the latest run
report: check_uv
	@bash -ec 'source scripts/loadenv.bash && load_root_env && cd backend && uv run python -m sqft.cli validate'
