from datetime import timedelta
from uuid import uuid4

from app import db, rules, starter_pack
from app.evaluator import drain
from app.ingestion import ingest
from app.ontology import Registry
from app.schemas import Confirmation, RuleConfig
from app.seed import import_inventory, seed

from .synthetic import readings


def demo(engine, confirmed=False):
    if not confirmed:
        raise ValueError(
            "Demo creates a synthetic reviewed rule. Pass --confirm-review explicitly."
        )
    seed(engine)
    with db.transaction(engine) as conn:
        if db.rows(conn, db.versions) or db.rows(conn, db.telemetry):
            raise ValueError(
                "Use a fresh local demo database; refusing to overwrite existing data."
            )
        config = RuleConfig(
            name="Tenant comfort · Supply air deviation", overrides={"demo-b": {"threshold": 4}}
        )
        v = rules.create(conn, config)
        preview = Registry(conn).preview(config)
        v = rules.activate(
            conn,
            v,
            Confirmation(
                confirmed=True,
                preview_digest=preview["digest"],
                reviewer="Local synthetic demo operator",
            ),
        )
        start = db.utcnow() - timedelta(minutes=20)
        activation = {
            **v["activation"],
            "event_time_start": db.iso(start),
            "synthetic_replay": True,
        }
        conn.execute(
            db.versions.update().where(db.versions.c.id == v["id"]).values(activation=activation)
        )
        registry = Registry(conn)
        run_id = str(uuid4())
        for step in range(21):
            for event in readings(
                registry, start + timedelta(minutes=step), step, "sustained-fault", run_id=run_id
            ):
                ingest(conn, event)
            drain(conn, force=True)
        db.log(conn, "synthetic_demo_created", official_assessment_data=False)


def pack_demo(engine, pack, confirmed=False):
    if not confirmed:
        raise ValueError("Pass --confirm-review for the explicit source replay demonstration")
    with db.transaction(engine) as conn:
        if db.rows(conn, db.versions) or conn.execute(db.telemetry.select().limit(1)).first():
            raise ValueError("Use a fresh source-replay database; existing data is preserved")
        import_inventory(conn, starter_pack.inventory(pack))
        config = RuleConfig(
            name="Office tenant AHUs · Supply-air deviation",
            overrides={"building-b": {"threshold": 2}},
        )
        version = rules.create(conn, config)
        preview = Registry(conn).preview(config)
        rules.activate(
            conn,
            version,
            Confirmation(
                confirmed=True,
                preview_digest=preview["digest"],
                reviewer="Source replay demonstration operator",
            ),
            source_replay_start="2026-01-15T08:00:00Z",
        )
        registry = Registry(conn)
    for delivery_at, events in starter_pack.batches(registry, pack):
        with db.transaction(engine) as conn:
            for event in events:
                ingest(conn, event)
            drain(conn, force=True)
            db.put(
                conn,
                db.health,
                "source-replay",
                {
                    "data": {
                        "delivery_at": delivery_at,
                        "status": "replaying",
                        "source": "candidate-starter-pack",
                    }
                },
            )
    with db.transaction(engine) as conn:
        db.put(
            conn,
            db.health,
            "source-replay",
            {
                "data": {
                    "delivery_at": delivery_at,
                    "status": "completed",
                    "source": "candidate-starter-pack",
                }
            },
        )
        db.log(conn, "source_replay_completed", source="candidate-starter-pack")
