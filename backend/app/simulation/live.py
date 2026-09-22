import hashlib
import json
import time
from uuid import uuid4

from redis import Redis
from sqlalchemy.engine import Engine

from app import db, starter_pack
from app.persistence.ontology import load_registry

from .options import LiveSourceOptions


def live_event(event, at, run_id, cycle):
    original_id = event.get("event_id", "source-error")
    digest = hashlib.sha256(original_id.encode()).hexdigest()[:24]
    source = {
        **event.get("source", {}),
        "mode": "live-source",
        "original_event_id": original_id,
        "original_device_timestamp": event.get("device_timestamp"),
    }
    return {
        **event,
        "event_id": f"live:{run_id}:{cycle}:{digest}",
        "device_timestamp": db.iso(at),
        "source": source,
    }


def live_source_simulate(
    engine: Engine,
    args: LiveSourceOptions,
    *,
    client: Redis,
    stream: str,
):
    if args.interval not in {15, 60}:
        raise ValueError("Interval must be 15 or 60 seconds")
    if args.wait_for_rule:
        while True:
            with engine.connect() as conn:
                if conn.execute(
                    db.versions.select().where(db.versions.c.status == "ACTIVE").limit(1)
                ).first():
                    break
            time.sleep(1)
    with engine.connect() as conn:
        registry = load_registry(conn)
    selected = args.buildings.split(",") if args.buildings else None
    if selected and any(registry.entities.get(b, {}).get("kind") != "Building" for b in selected):
        raise ValueError("Unknown building selection")
    run_id = str(uuid4())
    published = 0
    cycle = 0
    while args.steps == 0 or published < args.steps:
        for _, events in starter_pack.batches(registry, args.pack, selected):
            at = db.utcnow()
            frame = [live_event(event, at, run_id, cycle) for event in events]
            client.xadd(
                stream,
                {
                    "payload": json.dumps(
                        {"frame": frame, "delivery_at": db.iso(at), "mode": "live-source"}
                    )
                },
            )
            published += 1
            with db.transaction(engine) as conn:
                db.put(
                    conn,
                    db.health,
                    "source-simulator",
                    {
                        "data": {
                            "delivery_at": db.iso(at),
                            "status": "streaming",
                            "source": "candidate-starter-pack",
                            "cycle": cycle,
                            "published_frames": published,
                        }
                    },
                )
            if args.steps and published >= args.steps:
                return
            time.sleep(args.interval)
        cycle += 1
