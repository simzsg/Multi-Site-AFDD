import json
import time
from uuid import uuid4

from redis import Redis
from sqlalchemy.engine import Engine

from app import db
from app.persistence.ontology import load_registry

from .options import SyntheticOptions


def readings(registry, at, step, mode="normal", building_ids=None, run_id=None):
    run_id = run_id or "fixture"
    allowed = set()
    if building_ids:
        descendants = set(building_ids)
        for _ in range(5):
            descendants |= {
                e["target"]
                for e in registry.edges
                if e["source"] in descendants and e["relation"] == "hasPart"
            }
        equipment = {
            e["source"]
            for e in registry.edges
            if e["relation"] == "hasLocation" and e["target"] in descendants
        }
        allowed = {
            e["target"]
            for e in registry.edges
            if e["source"] in equipment and e["relation"] == "hasPoint"
        }
    for point in registry.entities.values():
        if "unit" not in point["data"] or (building_ids and point["id"] not in allowed):
            continue
        if point["data"].get("source") != "synthetic":
            continue
        kind = point["kind"]
        fault = mode in {"sustained-fault", "missing-data", "duplicate", "invalid", "OFF"} or (
            mode == "recovery" and step < 17
        )
        faulty_ahu = point["id"].startswith("demo-a-f1-ahu1-")
        values = {
            "Run_Status": 0 if mode == "OFF" else 1,
            "Alarm": 0,
            "Supply_Air_Temperature_Sensor": 21 if fault and faulty_ahu else 17,
            "Supply_Air_Temperature_Setpoint": 16,
            "Return_Air_Temperature_Sensor": 24,
            "Zone_Air_Temperature_Sensor": 23.5,
            "Humidity_Sensor": 48,
            "CO2_Sensor": 620,
            "Electrical_Power_Sensor": 42.5,
            "Electrical_Energy_Sensor": 1000 + step * 0.7,
        }
        if (
            mode == "missing-data"
            and faulty_ahu
            and kind == "Supply_Air_Temperature_Sensor"
            and 5 <= step <= 12
        ):
            continue
        event = {
            "event_id": f"{run_id}:{point['id']}:{step}",
            "point_id": point["id"],
            "device_timestamp": db.iso(at),
            "value": values[kind],
            "unit": point["data"]["unit"],
            "quality": "GOOD",
        }
        yield event
        if mode == "duplicate":
            yield dict(event)
        if mode == "invalid" and faulty_ahu and kind == "Supply_Air_Temperature_Sensor":
            yield {**event, "event_id": event["event_id"] + "-invalid", "unit": "wrong"}


def simulate(engine: Engine, args: SyntheticOptions, *, client: Redis, stream: str):
    run_id = str(uuid4())
    with engine.connect() as conn:
        registry = load_registry(conn)
    if args.buildings and any(
        registry.entities.get(b, {}).get("kind") != "Building" for b in args.buildings.split(",")
    ):
        raise ValueError("Unknown building")
    step = 0
    while args.steps == 0 or step < args.steps:
        for event in readings(
            registry,
            db.utcnow(),
            step,
            args.mode,
            args.buildings.split(",") if args.buildings else None,
            run_id,
        ):
            client.xadd(stream, {"payload": json.dumps(event)})
        step += 1
        time.sleep(args.interval)
