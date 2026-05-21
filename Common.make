# -----------------------------------------------------------------------------------------------------------
# Common Makefile for Code Red projects
# Version: 1.9.14
# Source: https://github.com/Bain/code-red-base/blob/main/Common.make
# -----------------------------------------------------------------------------------------------------------
# This Makefile provides a set of common commands to help manage Code Red projects.
#
# By convention:
#  - targets that are called by the user 
#    - are named 'target-name'
#    - have a .PHONY directive with a short "##" comment that describes the target
#  - "##" comments are automatically detected by the help target and displayed in the help message
#  - utility targets that are used by other targets
#    - are named 'target_name'
#    - are listed in .PHONY (no "##" comment — hidden from make help) so a file with the same name
#      cannot shadow the recipe
#
# Usage:
#   make <command>
#
# Available Commands:
#   help                    : Show this help message
#   build                   : Build all platform libraries & applications
#   check                   : Verify all required tools and env files exist
#   clean                   : Clean all project build artifacts and docker volumes
#   down                    : Stop and remove all containers
#   logs                    : Show logs for all containers
#   ping                    : Check health of all Docker services
#   run                     : Start all containers locally
#   run-debug               : Start containers in debug mode (attached, shows logs)
#   run-detached            : Start containers in detached mode (detached, no logs)
#   test                    : Run tests
#   lint                    : Run linters (frontend + backend)
#
# -----------------------------------------------------------------------------------------------------------

# Default target
all: help

# -----------------------------------------------------------------------------------------------------------
# Set some defaults 
# -----------------------------------------------------------------------------------------------------------

# Project name
PROJECT_NAME := Code Red Base

# Default shell to use
SHELL := /bin/bash

# Project root: directory of the *entry* makefile (first in MAKEFILE_LIST), not this file.
# Using $(lastword $(MAKEFILE_LIST)) would follow the included Common.make path — wrong when projects
# `include $CODE_RED_BASE/Common.make` (scripts/, frontend/, backend/ would resolve to the template).
COMMON_MAKEFILE_DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
LOGGER := source $(COMMON_MAKEFILE_DIR)scripts/log.bash &&

# Location of checkenv script (resolve relative to this file)
CHECKENV_SCRIPT := $(COMMON_MAKEFILE_DIR)scripts/checkenv.bash

# Expected dependency versions
UV_EXPECTED_VERSION := 0.7.11
PYTHON_EXPECTED_VERSION := 3.10.6
BUN_EXPECTED_VERSION := 1.3.11


# -----------------------------------------------------------------------------------------------------------
# Help (default target)
#
# This will display any PHONY target in the Makefile that has a comment that 
# starts with '##'. 
# -----------------------------------------------------------------------------------------------------------

.PHONY: help build check clean run run-debug down test lint ping 

.PHONY: help ## Show this help message
help:
	@$(LOGGER) log_banner
	@$(LOGGER) log_info "Available make targets:"
	@echo ""
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf " %-22s$(RESET) $(DIM)- %s$(RESET)\n", $$2, $$3}'
		@echo ""
	@$(LOGGER) log_info "Quick start"
	@echo " make run-detached && make ping"


# -----------------------------------------------------------------------------------------------------------
# Check environment and tools targets
# -----------------------------------------------------------------------------------------------------------

# Auto-detect Docker Compose command (v2 or v1)
DOCKER_COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

.PHONY: clean ## Clean all project build artifacts and docker volumes
clean: check_docker
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Cleaning project build artifacts and Docker resources"
	@$(LOGGER) log_indent log_dim "Stopping and removing project containers and volumes..."
	@$(DOCKER_COMPOSE) --profile default --profile debug down -v --remove-orphans 2>/dev/null || $(DOCKER_COMPOSE) down -v --remove-orphans
	@$(LOGGER) log_indent log_dim "Removing project build artifacts..."
	@rm -rf frontend/node_modules frontend/dist backend/.venv dist *.egg-info **/.mypy_cache **/.pytest_cache **/.ruff_cache
	@$(LOGGER) log_indent log_dim "Removing .env backup files..."
	@rm -f .env.bak .env.new
	@$(LOGGER) log_success "Clean complete"

# Check if Docker is installed
check_docker:
	@if command -v docker >/dev/null 2>&1; then \
		if docker compose version >/dev/null 2>&1; then \
			DOCKER_VERSION=$$(docker compose version | head -n1 | sed 's/.*version //' | cut -d',' -f1); \
			$(LOGGER) log_info_dim "docker compose $$DOCKER_VERSION is installed."; \
		elif command -v docker-compose >/dev/null 2>&1; then \
			DOCKER_VERSION=$$(docker-compose --version | sed 's/.*version //' | cut -d',' -f1); \
			$(LOGGER) log_info_dim "docker-compose $$DOCKER_VERSION is installed."; \
		else \
			$(LOGGER) log_error "Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose."; \
			exit 1; \
		fi \
	else \
		$(LOGGER) log_error "Docker is not installed."; \
		exit 1; \
	fi

# Check ruff is installed
check_ruff:
	@if ! ruff --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "ruff is not installed. You can install it with 'brew install ruff' or 'uv tool install ruff'"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "$$(ruff --version) is installed."; \
	fi

# Check if uv is installed and version matches expected version
check_uv:
	@if ! uv --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "uv is not installed. You can install it with e.g. 'brew install uv' or 'pip install uv'"; \
		exit 1; \
	else \
		UV_VERSION=$$(uv --version | cut -d' ' -f2); \
		EXPECTED_VERSION="$(UV_EXPECTED_VERSION)"; \
		if [ "$$(printf '%s\n%s\n' "$$EXPECTED_VERSION" "$$UV_VERSION" | sort -V | head -n1)" = "$$EXPECTED_VERSION" ]; then \
			$(LOGGER) log_info_dim "$$(uv --version) is installed."; \
		else \
			$(LOGGER) log_error "Expected uv version >= $$EXPECTED_VERSION, got $$UV_VERSION"; \
			$(LOGGER) log_warning "Please install the correct version: pip install uv>=$$EXPECTED_VERSION"; \
			exit 1; \
		fi \
	fi

# Check if bun is installed and version meets minimum
check_bun:
	@if ! bun --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "bun is not installed. Install it with 'curl -fsSL https://bun.sh/install | bash' or 'brew install bun'"; \
		exit 1; \
	else \
		BUN_VERSION=$$(bun --version); \
		EXPECTED_VERSION="$(BUN_EXPECTED_VERSION)"; \
		if [ "$$(printf '%s\n%s\n' "$$EXPECTED_VERSION" "$$BUN_VERSION" | sort -V | head -n1)" = "$$EXPECTED_VERSION" ]; then \
			$(LOGGER) log_info_dim "bun $$BUN_VERSION is installed."; \
		else \
			$(LOGGER) log_error "Expected bun version >= $$EXPECTED_VERSION, got $$BUN_VERSION"; \
			$(LOGGER) log_warning "Upgrade with: 'bun upgrade' or 'brew upgrade bun'"; \
			exit 1; \
		fi \
	fi

# Check Biome + oxlint are available via bunx (frontend devDependencies; run bun install in frontend/ if this fails).
# Skip when there is no frontend/ — minimal or backend-only checkouts must not fail `make check`.
check_biome:
	@FRONTEND_DIR="$(COMMON_MAKEFILE_DIR)frontend"; \
	if [ ! -d "$$FRONTEND_DIR" ]; then \
		$(LOGGER) log_info_dim "Skipping Biome/oxlint check (no frontend/ directory)."; \
		exit 0; \
	fi; \
	$(MAKE) check_bun; \
	cd "$$FRONTEND_DIR" && \
	if ! bunx @biomejs/biome --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "Biome (@biomejs/biome) is not available via bunx. Run: cd frontend && bun install"; \
		exit 1; \
	fi; \
	if ! bunx oxlint --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "oxlint is not available via bunx. Run: cd frontend && bun install"; \
		exit 1; \
	fi; \
	BIOME_LINE=$$(bunx @biomejs/biome --version 2>/dev/null | head -n1); \
	OX_LINE=$$(bunx oxlint --version 2>/dev/null | head -n1); \
	$(LOGGER) log_info_dim "biome ($$BIOME_LINE) and oxlint ($$OX_LINE) are available."

# Check if python is installed and version matches expected version
check_python:
	@PYTHON_CMD=""; \
	if python3 --version >/dev/null 2>&1; then \
		PYTHON_CMD="python3"; \
	elif python --version >/dev/null 2>&1; then \
		PYTHON_CMD="python"; \
	else \
		$(LOGGER) log_error "Neither python3 nor python is installed. You can install it with e.g. 'brew install python'"; \
		exit 1; \
	fi; \
	PYTHON_VERSION=$$($$PYTHON_CMD --version | cut -d' ' -f2); \
	EXPECTED_VERSION="$(PYTHON_EXPECTED_VERSION)"; \
	if [ "$$(printf '%s\n%s\n' "$$EXPECTED_VERSION" "$$PYTHON_VERSION" | sort -V | head -n1)" = "$$EXPECTED_VERSION" ]; then \
		$(LOGGER) log_info_dim "$$PYTHON_CMD $$PYTHON_VERSION is installed."; \
	else \
		$(LOGGER) log_error "Required Python version >= $$EXPECTED_VERSION, got $$PYTHON_VERSION"; \
		$(LOGGER) log_warning "Please install the correct version or use pyenv: pyenv install $$EXPECTED_VERSION"; \
		exit 1; \
	fi

# Check all dependencies
check_deps:
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Checking Dependencies"
	@$(MAKE) check_docker
	@$(MAKE) check_biome
	@$(MAKE) check_uv
	@$(MAKE) check_ruff
	@$(MAKE) check_python


# Check environment variables
check_env:
	@$(CHECKENV_SCRIPT) .env


.PHONY: check ## Verify all required tools and env files exist
check: check_deps check_env


# -----------------------------------------------------------------------------------------------------------
# Security targets
#
# Security tooling runs in a standalone lane — make check and check_deps are untouched.
#
# One-time setup:  make setup-security
# Manual scan:     make check-security
# Image scan:      make scan-image IMAGE=myimage:tag
#
# `make setup-security` provisions Python tools via uv tool install and Go binaries via brew.
# Individual check_* targets accept either install method (e.g. `brew install bandit` works too).
# Trivy excluded: March 2026 supply chain attack compromised the binary and GitHub Action.
# pip-audit excluded: osv-scanner covers the same OSV database plus bun.lock in one pass.
# -----------------------------------------------------------------------------------------------------------

# Verify pre-commit is installed
check_precommit:
	@if ! pre-commit --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "pre-commit is not installed. You can install it with 'brew install pre-commit' or 'uv tool install pre-commit'"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "$$(pre-commit --version) is installed."; \
	fi

# Verify bandit is installed
check_bandit:
	@if ! bandit --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "bandit is not installed. You can install it with 'brew install bandit' or 'uv tool install bandit'"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "bandit $$(bandit --version 2>&1 | head -n1) is installed."; \
	fi

# Verify detect-secrets is installed
check_detect_secrets:
	@if ! detect-secrets --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "detect-secrets is not installed. You can install it with 'brew install detect-secrets' or 'uv tool install detect-secrets'"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "detect-secrets $$(detect-secrets --version) is installed."; \
	fi

# Verify semgrep is installed
check_semgrep:
	@if ! semgrep --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "semgrep is not installed. You can install it with 'brew install semgrep' or 'uv tool install semgrep'"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "semgrep $$(semgrep --version) is installed."; \
	fi

# Verify checkov is installed
check_checkov:
	@if ! checkov --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "checkov is not installed. You can install it with 'brew install checkov' or 'uv tool install checkov'"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "checkov $$(checkov --version) is installed."; \
	fi

# Verify osv-scanner is installed
check_osv:
	@if ! osv-scanner --version >/dev/null 2>&1; then \
		$(LOGGER) log_error "osv-scanner is not installed. Run: brew install osv-scanner"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "osv-scanner $$(osv-scanner --version 2>/dev/null | head -n1 | awk '{print $$3}') is installed."; \
	fi

# Verify grype is installed
check_grype:
	@if ! grype version >/dev/null 2>&1; then \
		$(LOGGER) log_error "grype is not installed. Run: brew install grype"; \
		exit 1; \
	else \
		$(LOGGER) log_info_dim "grype $$(grype version 2>/dev/null | grep '^Version:' | awk '{print $$2}') is installed."; \
	fi

# Aggregate: verify all security tools are installed
check_security_tools:
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Checking security tools"
	@$(MAKE) check_precommit
	@$(MAKE) check_bandit
	@$(MAKE) check_detect_secrets
	@$(MAKE) check_semgrep
	@$(MAKE) check_checkov
	@$(MAKE) check_osv
	@$(MAKE) check_grype

.PHONY: setup-security ## Install security tools and activate pre-commit git hook
setup-security:
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Installing Python tools via uv"
	@uv tool install pre-commit
	@uv tool install bandit
	@uv tool install detect-secrets
	@uv tool install semgrep
	@uv tool install checkov
	@uv tool install ruff
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Installing Go security tools via brew"
	@brew install osv-scanner grype
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Installing pre-commit git hook"
	@pre-commit install
	@$(LOGGER) log_info "Generating secrets baseline"
	@detect-secrets scan > .secrets.baseline
	@$(LOGGER) log_success "Generated .secrets.baseline — commit this file"
	@$(LOGGER) log_success "Security hooks installed. Run 'make check-security' to verify."

.PHONY: setup-hooks
setup-hooks:
	@$(LOGGER) log_warning "'make setup-hooks' is deprecated and will be removed in a future release. Use 'make setup-security' instead."
	@$(MAKE) setup-security

.PHONY: check-security ## Run all pre-commit security checks against the full codebase
check-security: check_security_tools
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Running security checks"
	@pre-commit run --all-files
	@$(LOGGER) log_success "Security checks passed"

.PHONY: scan-image ## Scan a Docker image for vulnerabilities with Grype (usage: make scan-image IMAGE=name:tag)
scan-image: check_grype
	@if [ -z "$(IMAGE)" ]; then \
		$(LOGGER) log_error "IMAGE is required. Usage: make scan-image IMAGE=myimage:tag"; \
		exit 1; \
	fi
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Scanning image: $(IMAGE)"
	@grype $(IMAGE)
	@$(LOGGER) log_success "Image scan complete"


# -----------------------------------------------------------------------------------------------------------
# Docker Compose container targets
# -----------------------------------------------------------------------------------------------------------

.PHONY: build ## Build all platform libraries & applications
build: check 
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Building Docker images"
	$(DOCKER_COMPOSE) --profile default --profile debug build 

.PHONY: run ## Start all containers locally
run: check
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Starting all containers"
	@$(LOGGER) log_info "Containers will run in foreground. Press Ctrl+C to stop."
	$(DOCKER_COMPOSE) --profile default up --build
	@$(LOGGER) log_success "All containers started"

.PHONY: run-debug ## Start containers in debug mode (attached, shows logs)
run-debug: check
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Starting all containers in debug mode (attached, shows logs)"
	@$(LOGGER) log_info "Containers will run in foreground. Press Ctrl+C to stop."
	$(DOCKER_COMPOSE) --profile debug up --build

.PHONY: run-detached ## Start containers in detached mode (detached, no logs)
run-detached: check
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Starting all containers in detached mode (background, no logs)"
	@$(LOGGER) log_info "Containers will run in background. Use 'make logs' to see logs."
	$(DOCKER_COMPOSE) --profile default up -d --build
	@$(LOGGER) log_success "All containers started"

.PHONY: logs ## Show logs for all containers
logs:
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Showing logs for all containers"
	@$(LOGGER) log_dim "Press Ctrl+C to exit"
	@$(DOCKER_COMPOSE) --profile default --profile debug logs -f || true

.PHONY: down ## Stop and remove all containers
down:
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Stopping all Docker containers..."
	@$(DOCKER_COMPOSE) --profile default --profile debug down 2>/dev/null || $(DOCKER_COMPOSE) down
	@$(DOCKER_COMPOSE) down --remove-orphans 2>/dev/null || true
	@$(LOGGER) log_success "All containers stopped"


# -----------------------------------------------------------------------------------------------------------
# Testing targets
# -----------------------------------------------------------------------------------------------------------

# backend_tests / frontend_tests are internal helpers (snake_case, not listed in make help).
.PHONY: backend_tests frontend_tests

backend_tests: check_uv
	@$(LOGGER) log_info_dim "Running backend tests"
	@cd "$(COMMON_MAKEFILE_DIR)backend" && uv run pytest

frontend_tests:
	@if [ ! -d "$(COMMON_MAKEFILE_DIR)frontend" ]; then \
		$(LOGGER) log_info_dim "Skipping frontend tests (frontend/ directory not found)."; \
		exit 0; \
	fi
	@$(MAKE) check_bun
	@cd "$(COMMON_MAKEFILE_DIR)frontend" && \
	if grep -qE '"test"[[:space:]]*:' package.json 2>/dev/null; then \
		$(LOGGER) log_info_dim "Running frontend tests"; \
		bun run test; \
	else \
		$(LOGGER) log_info_dim "Skipping frontend tests (no test script in package.json)."; \
	fi

.PHONY: test ## Run tests
test: check
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Running tests"
	@$(MAKE) backend_tests
	@$(MAKE) frontend_tests

# -----------------------------------------------------------------------------------------------------------
# Linting targets
# -----------------------------------------------------------------------------------------------------------

# backend_lint / frontend_lint are internal helpers (snake_case, not listed in make help).
.PHONY: backend_lint frontend_lint

backend_lint: check_uv
	@$(LOGGER) log_info_dim "Linting backend (ruff)"
	@cd "$(COMMON_MAKEFILE_DIR)backend" && uv run ruff check . && uv run ruff format --check .

frontend_lint:
	@if [ ! -d "$(COMMON_MAKEFILE_DIR)frontend" ]; then \
		$(LOGGER) log_info_dim "Skipping frontend lint (no frontend directory)."; \
		exit 0; \
	fi
	@$(MAKE) check_bun
	@cd "$(COMMON_MAKEFILE_DIR)frontend" && \
	if grep -qE '"lint"[[:space:]]*:' package.json 2>/dev/null; then \
		$(LOGGER) log_info_dim "Linting frontend (biome + oxlint)"; \
		bun run lint; \
	else \
		$(LOGGER) log_info_dim "Skipping frontend lint (no lint script in package.json)."; \
	fi

.PHONY: lint ## Run linters on frontend and backend
lint: check
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Running linters"
	@$(MAKE) backend_lint
	@$(MAKE) frontend_lint

# curl timeouts: without --max-time, curl can hang if a service accepts TCP but never completes the response
# (e.g. uvicorn mid-reload). --connect-timeout caps the TCP handshake; --max-time caps the whole request.
PING_CURL_OPTS := -sS --connect-timeout 2 --max-time 3

.PHONY: ping ## Check health of all Docker services
ping:
	@$(LOGGER) log_separator
	@$(LOGGER) log_info "Checking health of ${PROJECT_NAME} services"
	@echo ""
	@echo " Application Services:"
	@echo -e "  • Frontend $(DIM)(Node.js)$(RESET) $(BLUE)[http://localhost:3000]$(RESET)"
	@if curl $(PING_CURL_OPTS) http://localhost:3000 >/dev/null 2>&1; then \
		$(LOGGER) log_indent log_success "Frontend is healthy"; \
	else \
		$(LOGGER) log_indent log_error "Frontend is not responding"; \
	fi
	@echo -e "  • Backend API $(DIM)(FastAPI)$(RESET) $(BLUE)[http://localhost:8000]$(RESET)"
	@if curl $(PING_CURL_OPTS) http://localhost:8000/health >/dev/null 2>&1; then \
		$(LOGGER) log_indent log_success "Backend API is healthy"; \
	else \
		$(LOGGER) log_indent log_error "Backend API is not responding"; \
	fi
	@echo ""
	@echo " Database Services:"
	@echo -e "  • PostgreSQL $(DIM)(pgvector/pg16)$(RESET) $(BLUE)[localhost:5432]$(RESET)"
	@if nc -z localhost 5432 >/dev/null 2>&1 || timeout 1 bash -c 'echo > /dev/tcp/localhost/5432' 2>/dev/null; then \
		$(LOGGER) log_indent log_success "PostgreSQL is healthy"; \
	else \
		$(LOGGER) log_indent log_error "PostgreSQL is not responding"; \
	fi
	@echo ""
	@$(LOGGER) log_info "Health check complete"



