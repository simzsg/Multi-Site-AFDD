# Multi-Site AFDD

Multi-Site AFDD is a working building-operations prototype for turning engineering knowledge into safe, reusable and explainable monitoring rules. It ingests the supplied three-building telemetry through Redis Streams, stores current values and TimescaleDB history, resolves equipment through an ontology, evaluates versioned AFDD rules and presents evidence through a React dashboard.

The implemented journey is: describe a rule, inspect the structured interpretation and matched assets, confirm activation, stream or replay telemetry, investigate the resulting issue and trace the AHU through its served zone to potentially affected rooms.

## Quickstart

Prerequisites are Docker Desktop with Docker Compose v2 and at least 4 GB of available memory.

```sh
cp .env.example .env
docker compose up --build -d --wait
```

Open the dashboard at <http://127.0.0.1:5173> and OpenAPI at <http://127.0.0.1:8000/docs>. The simulator waits for an active rule, then continuously publishes values derived from the supplied pack every 60 seconds. Set `SOURCE_INTERVAL=15` for a faster live demonstration.

Check service state with:

```sh
docker compose ps
curl -fsS http://127.0.0.1:5173/api/health
curl -fsS http://127.0.0.1:5173/api/pipeline-health
```

Stop the platform without deleting data with `docker compose down`. Add `--volumes` only when the PostgreSQL and Redis data may be discarded.

## Data lifecycle commands

The `init` service automatically runs migrations and imports the supplied inventory during startup. Explicit commands are available for review and recovery:

```sh
docker compose run --rm api python -m app.runtime migrate
docker compose run --rm api python -m app.runtime seed
docker compose run --rm api python -m app.runtime reset --confirm-reset
```

The live simulator uses current timestamps and new event IDs while retaining the original source identity and observation time in provenance:

```sh
docker compose run --rm simulator python -m app.runtime live-source-simulate --interval 15 --wait-for-rule
```

The deterministic replay preserves supplied event IDs, timestamps, duplicates and out-of-order delivery:

```sh
docker compose run --rm simulator python -m app.runtime source-simulate --acceleration 600 --wait-for-rule
```

Use `--buildings building-a,building-b` to select buildings and `--steps N` for a bounded simulator run.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `POSTGRES_PASSWORD` | Local PostgreSQL credential | `afdd-local-only` |
| `SOURCE_INTERVAL` | Live source interval; `15` or `60` seconds | `60` |
| `SOURCE_REPLAY_START` | Event-time activation boundary for deterministic replay | `2026-01-15T08:00:00Z` |
| `OPENAI_API_KEY` | Optional server-side model credential | unset |
| `OPENAI_MODEL` | Optional Responses API model name | unset |

No browser code receives the model credential. With no model configured, the UI exposes the bounded exact-example demo mode; the server integration remains ready for a reviewer-provided key and model.

## Verification

Create the local Python environment and frontend dependencies once if they are absent, then run:

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
npm ci --prefix frontend
./scripts/check.sh
npm run test:e2e --prefix frontend
```

The check covers formatting, 51 backend tests and the production frontend build. Browser tests cover the investigation journey, reviewed activation, responsive layout, live 3D telemetry, point history and the WebGL fallback. The real Redis integration test is opt-in through `AFDD_TEST_REDIS_URL`; the Docker smoke path exercises Redis, PostgreSQL, TimescaleDB and the workers together.

## Repository map

- `backend/app/api`: HTTP delivery layer
- `backend/app/application`: application orchestration
- `backend/app/persistence`: read-side database queries
- `backend/app/simulation`: deterministic replay, continuous source simulation and synthetic fixtures
- `backend/app/workers`: Redis ingestion and AFDD evaluation workers
- `backend/migrations`: Alembic schema history
- `frontend/src/components`: dashboard and equipment components
- `data/candidate-starter-pack`: unmodified authoritative assessment input
- `docs`: architecture, domain behavior, decisions, limitations and demonstration evidence

## Technical documents

- [Understanding checkpoint](docs/understanding-checkpoint.md)
- [System architecture](docs/architecture.md)
- [Brickschema model](docs/brickschema.md)
- [AFDD behavior](docs/afdd.md)
- [AI rule-authoring design](docs/ai-rule-authoring.md)
- [Technical decisions](docs/decisions.md)
- [Known limitations](docs/limitations.md)
- [Demonstration guide](docs/demo.md)
- [Usability measurement](docs/usability.md)

The current scope excludes physical gateways, equipment control and work orders. Historical backtesting and MCP access remain optional extensions. Production authentication and tenant isolation are called out in the limitations rather than represented as completed features.
