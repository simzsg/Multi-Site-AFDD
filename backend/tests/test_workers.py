import json

import pytest
from app import db
from app.workers.evaluation import EvaluationWorker
from app.workers.ingestion import IngestionWorker
from test_core import event


class StopWorker(Exception):
    pass


class DeliveryBroker:
    def __init__(self, engine, payload, expected_rows, expected_rejections):
        self.engine = engine
        self.payload = payload
        self.expected_rows = expected_rows
        self.expected_rejections = expected_rejections
        self.acked = False

    def xgroup_create(self, *args, **kwargs):
        pass

    def xautoclaim(self, *args, **kwargs):
        return ["0-0", [("1-0", {"payload": self.payload})]]

    def xpending(self, *args):
        return {"pending": 1}

    def xack(self, *args):
        with self.engine.connect() as conn:
            assert len(db.rows(conn, db.telemetry)) == self.expected_rows
            rejected = [r for r in db.rows(conn, db.audit) if r["action"] == "rejected"]
            assert len(rejected) == self.expected_rejections
            assert db.rows(conn, db.health)[0]["data"]["heartbeat_at"]
        self.acked = True
        raise StopWorker


class Broker:
    def __init__(self):
        self.messages = []
        self.acknowledged = []
        self.reads = 0

    def xgroup_create(self, stream, group, **kwargs):
        assert stream == "isolated-stream"

    def xautoclaim(self, *args, **kwargs):
        assert kwargs["min_idle_time"] == 30000
        return ["0-0", self.messages]

    def xreadgroup(self, *args, **kwargs):
        self.reads += 1
        return []

    def xpending(self, *args):
        return {"pending": len(self.messages)}

    def xack(self, stream, group, identity):
        self.acknowledged.append(identity)


@pytest.mark.parametrize(
    ("payload", "expected_rows", "expected_rejections"),
    [
        (
            json.dumps(
                {
                    "frame": [
                        event("Run_Status", 0, 1),
                        event("Supply_Air_Temperature_Sensor", 0, 21),
                    ]
                }
            ),
            2,
            0,
        ),
        ("{invalid", 0, 1),
        (json.dumps({"frame": [None] * 2001}), 0, 1),
    ],
)
def test_delivery_commits_all_frame_effects_before_ack(
    engine, payload, expected_rows, expected_rejections
):
    broker = DeliveryBroker(engine, payload, expected_rows, expected_rejections)
    with pytest.raises(StopWorker):
        IngestionWorker(engine, broker).run_forever()
    assert broker.acked


def test_delivery_rolls_back_and_does_not_ack_on_database_failure(engine, monkeypatch):
    broker = DeliveryBroker(engine, json.dumps({"frame": [event("Run_Status", 0, 1)]}), 1, 0)
    original_put = db.put

    def fail_heartbeat(conn, table, key, value):
        if table is db.health and "heartbeat_at" in value["data"]:
            raise RuntimeError("database write failed")
        return original_put(conn, table, key, value)

    monkeypatch.setattr(db, "put", fail_heartbeat)
    with pytest.raises(RuntimeError, match="database write failed"):
        IngestionWorker(engine, broker).run_forever()
    assert not broker.acked
    with engine.connect() as conn:
        assert not db.rows(conn, db.telemetry)
        assert not db.rows(conn, db.receipts)
        assert not db.rows(conn, db.outbox)


def test_single_cycle_prioritizes_reclaim_and_idle_heartbeat(engine):
    broker = Broker()
    broker.messages = [("1-0", {"payload": json.dumps(event("Run_Status", 0, 1))})]
    worker = IngestionWorker(engine, broker, stream="isolated-stream")
    assert worker.run_once() == 1
    assert broker.acknowledged == ["1-0"]
    assert broker.reads == 0
    broker.messages = []
    assert worker.run_once() == 0
    assert broker.reads == 1
    with engine.connect() as conn:
        health = db.rows(conn, db.health)[0]["data"]
        assert health["broker_pending"] == 0
        assert health["last_device_timestamp"]


def test_ack_failure_redelivery_has_one_business_effect(engine, monkeypatch):
    broker = Broker()
    worker = IngestionWorker(engine, broker, stream="isolated-stream")
    fields = {"payload": json.dumps(event("Run_Status", 0, 1))}
    original_ack = broker.xack

    def lost_ack(*args):
        raise ConnectionError("connection lost after database commit")

    monkeypatch.setattr(broker, "xack", lost_ack)
    with pytest.raises(ConnectionError):
        worker.process_message("1-0", fields)
    monkeypatch.setattr(broker, "xack", original_ack)
    worker.process_message("1-0", fields)
    with engine.connect() as conn:
        assert len(db.rows(conn, db.telemetry)) == 1
        assert len(db.rows(conn, db.outbox)) == 1
        assert len([row for row in db.rows(conn, db.audit) if row["action"] == "duplicate"]) == 1


def test_evaluator_single_cycle_marks_idle_health(engine):
    assert EvaluationWorker(engine).run_once() == 0
    with engine.connect() as conn:
        assert db.rows(conn, db.health)[0]["data"]["status"] == "idle"
