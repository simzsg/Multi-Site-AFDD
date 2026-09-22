#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

docker compose build
docker compose up -d --wait database broker
docker compose stop simulator ingestion afdd-worker api frontend >/dev/null 2>&1 || true
docker compose run --rm --no-deps api python -m app.runtime reset --confirm-reset
docker compose run --rm --no-deps api python -m app.runtime pack-demo --confirm-review
docker compose up -d --wait
