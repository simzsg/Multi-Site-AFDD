#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
.venv/bin/ruff check backend scripts
.venv/bin/ruff format --check backend scripts
.venv/bin/pytest -q
npm run build --prefix frontend
