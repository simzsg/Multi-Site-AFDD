#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r backend/requirements.lock
fi
if [ ! -d frontend/node_modules ]; then
  npm ci --prefix frontend
fi
PYTHONPATH=backend .venv/bin/python -m app.runtime migrate
PYTHONPATH=backend .venv/bin/python -m app.runtime seed
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
npm run dev --prefix frontend
