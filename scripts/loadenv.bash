#!/bin/bash
# Source the repo-root .env into the current shell (export all variables).
# Used by Makefile targets and optional local scripts — never source backend/.env or frontend/.env.

# shellcheck source=scripts/log.bash
source "$(dirname "${BASH_SOURCE[0]}")/log.bash"

load_root_env() {
  local root
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  local env_file="${root}/.env"
  if [ ! -f "$env_file" ]; then
    log_warning "No ${env_file} — run make check to create from .env.example"
    return 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  return 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  load_root_env
fi
