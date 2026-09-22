# Known limitations

## Assessment scope

- Model integration is implemented but no credential, model selection or real-model evaluation result is bundled. The integrating team must provide both environment variables and run the evaluation matrix for its selected model.
- Historical backtesting and MCP access are optional extensions and are not implemented.
- The platform monitors and explains; it does not control equipment, create work orders or prove a mechanical root cause.

## Security

The Docker review stack binds HTTP ports to loopback but does not implement user authentication, role-based authorization or tenant isolation. Reviewer identity on activation is an asserted label, not a verified principal. Production use requires TLS, identity-provider integration, authorization checks, CSRF/session policy, rate limits, secret management and security audit logging.

The optional model credential is server-side and excluded from responses. Prompt input is treated as data and structured output is validated, but deployment should additionally apply tenant-level cost budgets and provider egress policy.

## Scale

The evaluator uses one active drain lock. Bounded outbox batches protect transaction size, but one leader eventually limits throughput. Partition ownership by site or rule family is required before high-rate deployment.

The registry loads one ontology into memory per operation. Adjacency indexing makes traversal efficient for the current portfolio, but hundreds of sites need tenant-scoped ontology revisions and a bounded cache.

The dashboard polls portfolio snapshots every ten seconds. Issues are paginated, but inventory, relationships and current state are returned as complete portfolio snapshots. Larger portfolios need cursor-based changes, site-scoped queries or server-sent events.

Telemetry has point/time indexes but no retention, compression or continuous aggregate policies. These depend on agreed forensic retention and issue-evidence requirements. Audit and completed outbox records likewise need archival policy.

AI authoring is synchronous and can hold an HTTP request for a bounded model retry. Production authoring should run as an asynchronous job with idempotency keys, cancellation and per-tenant quotas.

## Availability and recovery

Compose runs one instance of each application service and does not provide database replication, broker failover, backups or cross-region recovery. Redis append-only persistence reduces local message loss but PostgreSQL remains the durable record. Recovery procedures and restore testing are deployment responsibilities.

The live simulator is intentionally a long-running review service. Deterministic fixture replay is separate and should be used for exact expected outcomes.

## Semantics

Brick `1.4.4` is pinned by this repository because the supplied pack contains no actual version value. The assessment-requested Brick location classes are exposed even though Brick 1.4 deprecates them in favor of RealEstateCore. `IAQ_Device` is an application class because the assessment specifies its point classes but not a Brick class for the combined device.

The platform exposes a semantic mapping rather than storing RDF triples or running a SHACL reasoner. New kinds and relationships require an explicit mapping change and compatibility test.

## Frontend

The lazy Three.js equipment scene is approximately 558 KB minified before gzip and about 141 KB gzip. Core readings remain available through HTML and table views if WebGL fails. A production rollout should measure load time on site networks and consider lower-detail geometry or renderer splitting.

The usability measurement is an automated benchmark of the primary investigation route. A moderated study with property engineers is still required to validate terminology, confidence and operational usefulness.
