#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Optional: if --profile <name> is passed, activate that profile first
if [[ "${1:-}" == "--profile" ]]; then
  PROFILE="${2:-dev}"
  shift 2 || true
  
  read -p "Activate profile '$PROFILE'? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    "${PROJECT_ROOT}/scripts/select_profile.sh" "${PROFILE}"
  else
    echo "Cancelled."
    exit 1
  fi
fi

# Launch interpreter (loads config directly from YAML)
exec "${PROJECT_ROOT}/.venv_openinterpreter/bin/python" "${PROJECT_ROOT}/scripts/openinterpreter_launcher.py" "$@"

