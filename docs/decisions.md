# Technical decisions

## PostgreSQL and TimescaleDB as one transactional foundation

Telemetry history uses a TimescaleDB hypertable while inventory, current state, receipts, rules, issues, requests, health, audit and outbox use normal PostgreSQL tables. This keeps event receipt, telemetry insertion, current projection and outbox publication atomic.

A separate time-series service would isolate load but introduce distributed consistency and a second operational surface. The shared foundation is appropriate for the assessment and moderate multi-site use. At larger scale, telemetry can be partitioned by tenant/site while relational metadata remains in PostgreSQL.

## Redis Streams for transport

Redis Streams supplies consumer groups, pending-message recovery and explicit acknowledgement with low local operational cost. The ingestion worker acknowledges only after the database transaction commits. PostgreSQL event receipts remain the source of business idempotency, so Redis redelivery is safe.

Kafka would provide stronger partitioning and long retention but is disproportionate for a three-building review stack. Redis persistence is enabled; PostgreSQL remains the durable system of record.

## Relational ontology with a semantic mapping layer

Entities and edges are stored relationally because the required graph is small, changes with inventory transactions and needs predictable local startup. Registry adjacency indexes make traversal proportional to the relevant neighborhood rather than the full edge set. A versioned mapping layer exposes Brick and QUDT URIs.

An RDF or graph database would add native reasoning and SHACL validation but also another store, migration path and failure mode. The API representation allows a later RDF projection without changing point IDs or AFDD evidence.

## Durable outbox between ingestion and evaluation

Ingestion writes the outbox in the same transaction as telemetry. This prevents accepted telemetry from being lost between persistence and evaluation. Evaluator transactions mark rows complete only after state and issue writes succeed.

Publishing a second broker message after commit would be faster to fan out but creates a dual-write failure window. The database outbox is simpler and replayable.

## Deterministic event-time evaluator

Device timestamp drives ordering, freshness and duration. Receipt timestamp is used only for transport lag and the short live-frame collection watermark. This makes supplied replay outcomes reproducible and prevents network delay from changing fault timing.

One evaluator drain owns state transitions through a PostgreSQL advisory try-lock. The choice favors correctness and easy recovery. Future throughput scaling should assign a stable partition owner per site or rule family rather than run competing evaluators against the same state.

## Immutable rule versions and preview digest

Editing creates a new draft. Activation recomputes validation and target preview, then requires the exact reviewed digest. Active issue evidence stores the opening configuration and effective override. This prevents ontology drift or later edits from changing the explanation of an existing issue.

## Continuous simulation and deterministic replay are separate

Live simulation cycles values from the supplied pack using new current timestamps and event IDs while retaining original provenance. Deterministic replay preserves source IDs, timestamps, duplicates and delivery order. Separating them avoids weakening reproducibility merely to keep a container running.

The first live frame declares a timeline transition, so the historical replay-to-live time jump is not counted as an equipment data gap. Missing intervals within the live timeline remain visible.

## Server-side AI boundary

The model proposes a strict structured draft; deterministic services own validation, identity resolution, preview and activation. One retry can use validation feedback. Credentials remain server-side and real-model selection is deferred to the integrating environment.

## React workspace and lazy Three.js scene

The product uses one coherent drill-down workspace because the hero journey crosses portfolio, issue, rule and pipeline context. UI capabilities are split into components, while a memoized ontology hook owns graph lookups. Three.js is lazy-loaded and has a usable no-WebGL fallback. The separate scene chunk remains large, so production delivery should measure whether the visual benefit justifies its network cost.

The dashboard uses system font stacks so startup and screenshot capture remain reproducible without third-party font availability.
