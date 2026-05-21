# Version: 1.4

# AGENTS.md — Code Red Base

> **Applies to:** All files (always active)

This repo is an **installer template**, not a standalone application.
Its files are copied into other projects via `scripts/install.bash`.
Do not treat it as a production app or add project-specific business logic here.

---

# Core Principles

- Keep this repo minimal — it is scaffolding, not a product.
- Remove what is not needed; delete unused or deprecated code.
- One pattern per problem. Extend existing utilities rather than adding new ones.
- Do not create summary or documentation files (e.g. `IMPLEMENTATION_SUMMARY.md`).
- Do not document fixes here — use PRs and git history for context.
- Test pragmatically; focus on practical coverage of real behavior.

---

# Build System

`make` is the **only** entrypoint for all build, run, test, and check operations. Never suggest `npm run`, `python ...`, or `docker compose ...` directly — wrap everything in a `make` target.

All targets live in `Common.make` and are exposed via the root `Makefile`. Do not bypass Make to run `docker compose` or scripts directly.

| Target              | Purpose                                   |
| ------------------- | ----------------------------------------- |
| `make run`          | Start all containers in foreground        |
| `make run-detached` | Start all containers detached             |
| `make run-debug`    | Start with debug profile (port 9229)      |
| `make build`        | Build all containers                      |
| `make check`        | Verify all required tools and env files   |
| `make down`         | Stop and remove containers                |
| `make clean`        | Remove build artifacts and Docker volumes |
| `make ping`         | Health check all running services         |
| `make test`         | Run test suite                            |
| `make lint`         | Run frontend and backend linters          |
| `make logs`         | Show container logs                       |
| `make help`         | List all user-facing targets              |

**Quick start:**

```bash
make check          # verify env + deps first
make run-detached   # start in background
make ping           # confirm healthy
```

Key files:

- `Common.make` — all shared targets and dependency checks
- `scripts/install.bash` — copies versioned bundles from this repo into target projects (`--interactive`, `--bundle`, `--update`, `--dry-run`)
- `scripts/checkenv.bash` — validates `.env` against `.env.example`
- `scripts/log.bash` — colored logging utilities used throughout Make targets

---

# Environment Configuration

- **One `.env` at the project root. No exceptions.**
- Never create `frontend/.env`, `backend/.env`, or any service-level env files.
- `.env.example` is the source of truth — always add new variables there first.
- `.env` is generated from `.env.example` by `scripts/checkenv.bash` on first run.
- `make check` validates that all required variables are present and non-empty.
- Fail fast on missing config — never use defaults to mask missing critical settings.
- `docker-compose.yml` loads the root `.env` via `env_file: .env`.

---

# Frontend

- Runtime: Next.js + React + TypeScript, port 3000.
- UI components: Tailwind CSS v4 + shadcn.
- Package manager: **Bun** (≥1.3.11). Do **not** use npm or yarn.
- Install deps: `bun install`. Run dev: `bun run dev`.
- Linting: **Biome** (format + lint) and **Oxlint**.
- Do not add `.env` files inside `frontend/`.

---

# Backend

- Currently a placeholder directory for a future Python/FastAPI service (port 8000).
- Python package manager: **uv** (≥0.7.11). Do not use pip directly.
- Linting and formatting: **Ruff** per project config. Run `ruff check` and `ruff format`.
- Do not add `.env` files inside `backend/`.

---

# Docker

- Three services: `postgres_db` (pgvector/pg16, port 5432), `frontend` (default profile), `frontend-debug` (debug profile, adds port 9229).
- Use `make run` (default profile) or `make run-debug` (debug profile).
- Database host inside Docker is `pgvector` (the service name), not `localhost`.
- Infrastructure only in `docker-compose.yml` — no business logic.

---

# scripts/checkenv.bash

Validates `.env` files against `.env.example`. Called automatically by `make check` and `make run`.

```bash
# Check default .env
./scripts/checkenv.bash

# Check multiple files (e.g. multi-app project)
./scripts/checkenv.bash .env

# Non-interactive merge (CI/CD)
./scripts/checkenv.bash --merge

# Verbose output
./scripts/checkenv.bash --verbose .env
```

**Behavior:**

- Creates `.env` from `.env.example` if missing
- Reports missing or empty variables
- Offers interactive merge → writes `.env.new`, optionally replaces original with `.env.bak` backup
- `--merge` flag skips prompts (for CI)

---

# scripts/log.bash

Shared colored logging for all bash scripts. Always source it — never reimplement logging.

```bash
source "$(dirname "$0")/log.bash"

log "plain white message"
log_info "blue info"
log_success "green success"
log_warning "yellow warning"
log_error "red error"
log_dim "dimmed message"
log_separator         # full-width separator line
log_banner            # Code Red ASCII art banner
log_indent log_success "indented success"
log_verbose "only shown if VERBOSE=true"
```

If a project is missing `log.bash`, copy it from source — never reimplement it:

```bash
cp "$CODE_RED_BASE/scripts/log.bash" scripts/log.bash
```

---

# make help Pattern

The `help` target auto-discovers targets by scanning for `.PHONY` lines with a `##` comment. The description lives on the `.PHONY` line, and that line must sit **immediately above** its target definition — not batched at the top of the file.

```makefile
# ✅ Correct
.PHONY: build ## Build all containers
build: check
    ...

# ❌ Wrong — batched .PHONY at top won't appear in help
.PHONY: build clean
build: check ## this won't show in help
    ...
```

**Naming conventions:**

- `kebab-case` — user-facing targets; get a `##` description; appear in `make help`
- `snake_case` — internal utility targets (e.g. `check_uv`, `check_deps`); no `##` comment; hidden from `make help`

---

# Dependency Check Pattern

The canonical pattern for `check_*` targets in `Common.make`:

- Use `snake_case` for utility checks (`check_uv`, `check_ruff`) — internal, not listed in `make help`
- Use `kebab-case` for the public aggregate (`make check`) — user-facing
- Always log the found version on success with `log_info_dim` — not silence
- Use `sort -V` for semver `>=` comparisons — never string equality
- Aggregate checks call sub-targets via `$(MAKE)`, not inline

```makefile
# Version-gated check
check_uv:
    @UV_VERSION=$$(uv --version | cut -d' ' -f2); \
    if [ "$$(printf '%s\n%s\n' "$(UV_EXPECTED_VERSION)" "$$UV_VERSION" | sort -V | head -n1)" = "$(UV_EXPECTED_VERSION)" ]; then \
        $(LOGGER) log_info_dim "$$(uv --version) is installed."; \
    else \
        $(LOGGER) log_error "Expected uv >= $(UV_EXPECTED_VERSION), got $$UV_VERSION"; \
        exit 1; \
    fi

# Aggregate
check_deps:
    @$(MAKE) check_docker
    @$(MAKE) check_uv
    @$(MAKE) check_ruff

.PHONY: check ## Verify all required tools and env files
check: check_deps check_env
```

---

# File Layout

```
project-root/
├── Makefile              # includes Common.make; add project-specific targets here
├── Common.make           # all standard targets, logging, env check wiring
├── AGENTS.md             # AI assistant rules (this file)
├── CLAUDE.md             # Claude Code wrapper — imports AGENTS.md
├── .env                  # gitignored; created from .env.example
├── .env.example          # committed; source of truth for required vars
├── docker-compose.yml    # infrastructure only
├── .cursor/
│   └── rules/
│       └── base.mdc      # Cursor rules wrapper — references AGENTS.md
├── scripts/
│   ├── checkenv.bash     # env validation (installed from code-red-base)
│   └── log.bash          # colored logging utilities (installed from code-red-base)
├── .pre-commit-config.yaml
├── .semgrep/
├── .secrets.baseline
├── osv-scanner.toml
├── frontend/             # Next.js + Bun (optional; from code-red-base template)
└── backend/              # Python + uv (optional; from code-red-base template)
```

---

# $CODE_RED_BASE

The canonical code-red-base source lives at `$CODE_RED_BASE`. Always use this env var — never guess paths or search the filesystem.

```bash
# Read source files
cat "$CODE_RED_BASE/Common.make"
cat "$CODE_RED_BASE/scripts/log.bash"
cat "$CODE_RED_BASE/scripts/checkenv.bash"

# Copy a file into the current project
cp "$CODE_RED_BASE/scripts/log.bash" scripts/log.bash

# Bootstrap a new project
"$CODE_RED_BASE/scripts/install.bash" /path/to/target-project
```

**Before writing any code** that involves Make targets, logging, or env validation: read the actual source file via `cat "$CODE_RED_BASE/..."`. Do not reconstruct patterns from memory.

---

# Linting and Formatting

- Python: `ruff check` and `ruff format`. Fix code rather than suppressing rules.
- Frontend: `biome` (format + lint) and `oxlint`. Fix code, don't suppress rules.
- If suppression is unavoidable, scope it narrowly and justify in the PR.

---

# Security

Two-layer defence against OWASP Web Top 10 and LLM Top 10:

1. **Pre-commit hooks** — block issues at `git commit` (this PR)
2. **Claude Code hooks** — block issues at edit time (separate PR)

**One-time setup:**

```bash
make setup-security    # installs tools, wires git hook, generates .secrets.baseline
```

**Run manually:**

```bash
make check-security              # runs all hooks against the full codebase
make scan-image IMAGE=name:tag   # scan a built container image with Grype
```

## Tools and OWASP coverage

| Tool             | Installed via     | OWASP coverage                                           |
| ---------------- | ----------------- | -------------------------------------------------------- |
| `detect-secrets` | `uv tool install` | A02, LLM02 — secret and credential leakage               |
| `bandit`         | `uv tool install` | A03 — Python injection and insecure patterns             |
| `semgrep` (OSS)  | `uv tool install` | A01, A03, A05, A07, A10, LLM01, LLM05                    |
| `osv-scanner`    | `brew install`    | A06, A08, LLM03 — Python + JS deps (reads `bun.lock`)    |
| `checkov`        | `uv tool install` | A01, A05, A07, LLM06 — Docker + IaC misconfiguration     |
| `grype`          | `brew install`    | Container image scanning (manual, via `make scan-image`) |

**Trivy is excluded.** A March 2026 supply chain attack compromised the Trivy binary
(v0.69.4) and GitHub Action (75/76 tags poisoned) with a credential stealer targeting
SSH keys, cloud credentials, and Kubernetes tokens. Use Grype instead.

**pip-audit is excluded.** osv-scanner queries the same OSV database (PyPI advisories,
GitHub Security Advisories, NVD) and also reads `bun.lock` — equivalent Python coverage
plus JS/TS in one tool.

**checkov covers IaC in downstream projects.** This repo has no Terraform today, but
checkov automatically scans Terraform, CloudFormation, Kubernetes manifests, and ARM
templates in any project this template is installed into — no config change needed.

## Custom LLM rules

Starter semgrep rules for LLM-specific patterns live in `.semgrep/llm-rules.yaml`:

- **LLM01** — HTTP request data concatenated into prompts (prompt injection)
- **LLM05** — LLM output passed to shell, `eval`, or `innerHTML` (insecure output handling)

Add project-specific rules to `.semgrep/` — semgrep picks up all `.yaml` files in that directory.

## Categories not covered by tooling

These require design and architecture decisions — no pre-commit hook can replace them:

| Category                          | What to do instead                                         |
| --------------------------------- | ---------------------------------------------------------- |
| A04 Insecure Design               | Threat modelling and design review                         |
| A09 Logging Failures              | Runtime observability — structured logging, alerting       |
| LLM04 Model DoS                   | Rate limiting and cost controls in the API layer           |
| LLM07 System Prompt Leakage       | Store prompts with access controls, not in code            |
| LLM08 Vector/Embedding Weaknesses | Retrieval pipeline design and vector store access controls |
| LLM09 Misinformation              | Evaluation framework, RAG grounding, human review          |
| LLM10 Unbounded Consumption       | Runtime cost controls and per-user rate limits             |

---

# Output Format

When proposing changes, always include:

1. A short summary of the change and why it is needed.
2. File path(s) with approximate line numbers.
3. A minimal diff or patch block.

When suggesting changes to a project:

1. Propose changes as `make` targets or extensions to `Common.make` — not raw shell one-liners.
2. New env variables → add to `.env.example` first.
3. New bash scripts → source `scripts/log.bash` for consistent output.
4. Python changes → use `uv` for deps, `ruff` for lint/format.
5. Frontend changes → use `bun` (not npm), follow Next.js/Tailwind/shadcn conventions.
6. Only increase a version number in one of the Code Red Base files if we are in Code Red Base repo,  not if we are in a downstream user of Base.
