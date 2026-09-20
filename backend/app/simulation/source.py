import json
import time

from redis import Redis
from sqlalchemy.engine import Engine

from app import db, starter_pack
from app.ontology import Registry

from .options import SourceOptions


def source_simulate(engine: Engine, args: SourceOptions, *, client: Redis, stream: str):
    if args.acceleration <= 0:
        raise ValueError("Acceleration must be positive")
    if args.wait_for_rule:
        while True:
            with engine.connect() as conn:
                if any(v["status"] == "ACTIVE" for v in db.rows(conn, db.versions)):
                    break
            time.sleep(1)
    with engine.connect() as conn:
        registry = Registry(conn)
    selected = args.buildings.split(",") if args.buildings else None
    if selected and any(registry.entities.get(b, {}).get("kind") != "Building" for b in selected):
        raise ValueError("Unknown building selection")
    previous = None
    for delivery_at, events in starter_pack.batches(
        registry, args.pack, selected, args.steps or None
    ):
        if previous:
            time.sleep(
                max(0, (db.stamp(delivery_at) - db.stamp(previous)).total_seconds())
                / args.acceleration
            )
        client.xadd(stream, {"payload": json.dumps({"frame": events, "delivery_at": delivery_at})})
        previous = delivery_at
    with db.transaction(engine) as conn:
        db.put(
            conn,
            db.health,
            "source-replay",
            {
                "data": {
                    "delivery_at": previous,
                    "status": "published",
                    "source": "candidate-starter-pack",
                }
            },
        )
