#!/bin/sh
set -eu

compose=${COMPOSE_COMMAND:-docker compose}
base_url=${AFDD_FRONTEND_URL:-http://127.0.0.1:5173}

curl -fsS "$base_url/api/health" >/dev/null
$compose up -d --no-deps --force-recreate --wait api >/dev/null

attempt=0
while [ "$attempt" -lt 15 ]; do
  if curl -fsS "$base_url/api/health" >/dev/null; then
    echo "PASS: frontend proxy recovered after API container recreation"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 1
done

echo "Frontend proxy did not recover after API container recreation" >&2
exit 1
