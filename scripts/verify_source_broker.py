import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import redis
from app import db, rules, schema, starter_pack
from app.ontology import Registry
from app.schemas import Confirmation, RuleConfig
from app.seed import import_inventory
from sqlalchemy import func, select

url = os.environ["AFDD_TEST_REDIS_URL"]
client = redis.Redis.from_url(url, decode_responses=True)
stream = "source-integration-" + str(uuid4())
with tempfile.TemporaryDirectory(prefix="afdd-source-") as directory:
    database = f"sqlite:///{directory}/source.db"
    engine = db.connect(database)
    schema.upgrade(engine)
    with db.transaction(engine) as conn:
        import_inventory(conn, starter_pack.inventory())
        config = RuleConfig(overrides={"building-b": {"threshold": 2}})
        version = rules.create(conn, config)
        registry = Registry(conn)
        preview = registry.preview(config)
        rules.activate(
            conn,
            version,
            Confirmation(
                confirmed=True,
                preview_digest=preview["digest"],
                reviewer="Isolated real broker integration test",
            ),
            source_replay_start="2026-01-15T08:00:00Z",
        )
    env = {
        **os.environ,
        "DATABASE_URL": database,
        "REDIS_URL": url,
        "TELEMETRY_STREAM": stream,
        "PYTHONPATH": str(Path(db.__file__).resolve().parents[1]),
    }
    with open(f"{directory}/workers.log", "w") as log:
        processes = [
            subprocess.Popen(
                [sys.executable, "-m", "app.runtime", worker], env=env, stdout=log, stderr=log
            )
            for worker in ["ingestion", "evaluator"]
        ]
        try:
            for delivery_at, events in starter_pack.batches(registry):
                client.xadd(
                    stream, {"payload": json.dumps({"frame": events, "delivery_at": delivery_at})}
                )
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if not all(p.poll() is None for p in processes):
                    text_log = open(f"{directory}/workers.log").read()
                    trace_index = text_log.rfind("Traceback")
                    raise AssertionError(
                        "Worker exited: " + text_log[trace_index : trace_index + 9000]
                    )
                with engine.connect() as conn:
                    count = conn.execute(select(func.count()).select_from(db.telemetry)).scalar()
                    pending = conn.execute(
                        select(func.count())
                        .select_from(db.outbox)
                        .where(db.outbox.c.done.is_(False))
                    ).scalar()
                if count == 103655 and pending == 0:
                    verifier = Path(__file__).with_name("verify_pack.py")
                    subprocess.run([sys.executable, str(verifier)], env=env, check=True)
                    print(
                        "PASS: supplied source → real Redis → ingestion worker → durable outbox → evaluator worker"
                    )
                    break
                time.sleep(1)
            else:
                raise AssertionError(f"Source replay timeout: count={count}, pending={pending}")
        finally:
            for process in processes:
                process.terminate()
                process.wait(timeout=5)
            client.delete(stream)
            engine.dispose()
