import json
import os
import time
from uuid import uuid4

import httpx
from app import db
from app.schema import HEAD_REVISION
from redis import Redis
from sqlalchemy import text

client = httpx.Client(base_url="http://localhost:8000/api", timeout=10)
assert client.get("/health").json()["database"] == "postgresql"
assert len(client.get("/buildings").json()) == 3
engine = db.connect()
with engine.connect() as conn:
    assert (
        conn.execute(
            text(
                "SELECT COUNT(*) FROM timescaledb_information.hypertables WHERE hypertable_name = 'telemetry'"
            )
        ).scalar()
        == 1
    )
    assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == HEAD_REVISION
rule = client.post(
    "/rules", json={"name": "Compose integration smoke", "logic": {"duration_minutes": 0.05}}
).json()
preview = client.post(f"/rules/{rule['id']}/preview", json={}).json()
response = client.post(
    f"/rules/{rule['id']}/activate",
    json={
        "confirmed": True,
        "preview_digest": preview["digest"],
        "reviewer": "Compose integration test",
    },
)
response.raise_for_status()
redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
run = str(uuid4())
first = None
for step in range(8):
    at = db.iso(db.utcnow())
    for kind, value, unit in [
        ("Run_Status", 1, "bool"),
        ("Supply_Air_Temperature_Setpoint", 16, "C"),
        ("Supply_Air_Temperature_Sensor", 21, "C"),
    ]:
        event = {
            "event_id": f"{run}-{step}-{kind}",
            "point_id": {
                "Run_Status": "ahu-a-f01-east-run",
                "Supply_Air_Temperature_Setpoint": "ahu-a-f01-east-sat-sp",
                "Supply_Air_Temperature_Sensor": "ahu-a-f01-east-sat",
            }[kind],
            "device_timestamp": at,
            "value": value,
            "unit": unit,
            "quality": "GOOD",
        }
        first = first or event
        redis.xadd("telemetry", {"payload": json.dumps(event)})
    time.sleep(1)
redis.xadd("telemetry", {"payload": json.dumps(first)})
redis.xadd(
    "telemetry", {"payload": json.dumps({**first, "event_id": run + "-invalid", "unit": "wrong"})}
)
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    issues = [i for i in client.get("/issues").json() if i["version_id"] == rule["id"]]
    health = client.get("/pipeline-health").json()
    if issues and health["duplicates"] >= 1 and health["rejected"] >= 1:
        assert len(issues) == 1
        assert len(issues[0]["data"]["affected"]["rooms"]) == 2
        print(
            "PASS: Timescale hypertable, Redis ingestion, dedup/rejection, evaluator, issue evidence"
        )
        break
    time.sleep(1)
else:
    raise AssertionError("Pipeline did not produce expected smoke-test issue")
