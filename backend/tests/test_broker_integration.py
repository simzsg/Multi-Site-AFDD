import json
import os
import subprocess
import sys
import time
from uuid import uuid4

import pytest
import redis
from app import db, schema
from app.seed import seed
from app.workers.ingestion import IngestionWorker
from test_core import active, event


@pytest.mark.skipif(
    not os.getenv("AFDD_TEST_REDIS_URL"),
    reason="Set AFDD_TEST_REDIS_URL for real broker integration",
)
def test_worker_redelivery_outbox_and_reclaim(tmp_path):
    url = os.environ["AFDD_TEST_REDIS_URL"]
    stream = "test-" + str(uuid4())
    client = redis.Redis.from_url(url, decode_responses=True)
    database = "sqlite:///" + str(tmp_path / "integration.db")
    engine = db.connect(database)
    schema.upgrade(engine)
    seed(engine)
    with db.transaction(engine) as conn:
        active(conn)
    client.xgroup_create(stream, "ingestion", id="0", mkstream=True)
    first = event("Run_Status", 0, 1)
    client.xadd(stream, {"payload": json.dumps(first)})
    stranded = client.xreadgroup("ingestion", "crashed-consumer", {stream: ">"}, count=1)
    assert stranded
    env = {
        **os.environ,
        "DATABASE_URL": database,
        "REDIS_URL": url,
        "TELEMETRY_STREAM": stream,
        "PYTHONPATH": "backend",
    }
    log = open(tmp_path / "workers.log", "w")
    ingestion = subprocess.Popen(
        [sys.executable, "-m", "app.runtime", "ingestion"], env=env, stdout=log, stderr=log
    )
    evaluator = subprocess.Popen(
        [sys.executable, "-m", "app.runtime", "evaluator"], env=env, stdout=log, stderr=log
    )
    try:
        for minute in range(16):
            for kind, value in [
                ("Run_Status", 1),
                ("Supply_Air_Temperature_Sensor", 21),
                ("Supply_Air_Temperature_Setpoint", 16),
            ]:
                client.xadd(stream, {"payload": json.dumps(event(kind, minute, value))})
        client.xadd(
            stream, {"payload": json.dumps({**first, "event_id": "invalid-test", "unit": "wrong"})}
        )
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            assert ingestion.poll() is None, (tmp_path / "workers.log").read_text()
            assert evaluator.poll() is None, (tmp_path / "workers.log").read_text()
            with engine.connect() as conn:
                issues = db.rows(conn, db.issues)
                actions = [a["action"] for a in db.rows(conn, db.audit)]
                pending = [o for o in db.rows(conn, db.outbox) if not o["done"]]
            if (
                len(issues) == 1
                and "duplicate" in actions
                and "rejected" in actions
                and not pending
                and client.xpending(stream, "ingestion")["pending"] == 0
            ):
                break
            time.sleep(0.5)
        else:
            pytest.fail((tmp_path / "workers.log").read_text()[-5000:])
        assert len(issues[0]["data"]["observations"]) == 16
        assert len(issues[0]["data"]["affected"]["rooms"]) == 2
    finally:
        for process in (ingestion, evaluator):
            process.terminate()
            process.wait(timeout=5)
        log.close()
        client.delete(stream)
        engine.dispose()


def test_worker_commits_heartbeat_before_each_frame_ack(engine):
    class Finished(Exception):
        pass

    class Broker:
        def close(self):
            pass

        def xgroup_create(self, *args, **kwargs):
            pass

        def xautoclaim(self, *args, **kwargs):
            return [
                "0-0",
                [
                    ("1-0", {"payload": json.dumps({"frame": [event("Run_Status", 0, 1)]})}),
                    ("2-0", {"payload": "invalid JSON"}),
                ],
            ]

        def xpending(self, *args):
            return {"pending": 2}

        def xack(self, stream, group, identity):
            with engine.connect() as conn:
                health = db.rows(conn, db.health)[0]["data"]
                assert (db.utcnow() - db.stamp(health["heartbeat_at"])).total_seconds() < 2
                assert db.stamp(health["last_device_timestamp"]) == db.stamp(
                    event("Run_Status", 0, 1)["device_timestamp"]
                )
            if identity == "2-0":
                raise Finished

    with pytest.raises(Finished):
        IngestionWorker(engine, Broker()).run_forever()
