#!/usr/bin/env bash
# ==============================================================================
# SceneDiff Backend Quality Gate Pipeline
# Runs Ruff lint, Ruff format check, MyPy strict type checking, and Pytest.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

cd "${BACKEND_DIR}"

# Detect virtualenv python/bin if present
if [[ -f "${BACKEND_DIR}/.venv/bin/activate" ]]; then
    source "${BACKEND_DIR}/.venv/bin/activate"
elif [[ -f "${BACKEND_DIR}/.venv/Scripts/activate" ]]; then
    source "${BACKEND_DIR}/.venv/Scripts/activate"
fi

echo "=================================================="
echo "==> 1/4 Running Ruff Lint Check..."
echo "=================================================="
ruff check .

echo "=================================================="
echo "==> 2/4 Running Ruff Format Verification..."
echo "=================================================="
ruff format --check .

echo "=================================================="
echo "==> 3/4 Running MyPy Strict Type Checking..."
echo "=================================================="
mypy .

echo "=================================================="
echo "==> 4/4 Running Pytest Test Suite..."
echo "=================================================="
pytest -v

echo "=================================================="
echo "==> ALL QUALITY GATES PASSED! Ready for commit. <="
echo "=================================================="
