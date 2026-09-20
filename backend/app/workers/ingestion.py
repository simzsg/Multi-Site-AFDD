import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import Event
from uuid import uuid4

from redis import Redis, ResponseError
from sqlalchemy.engine import Connection, Engine

from app import db
from app.ingestion import ingest


@dataclass
class IngestionWorker:
    engine: Engine
    client: Redis
    stream: str = "telemetry"
    group: str = "ingestion"
    consumer: str = field(default_factory=lambda: f"consumer-{uuid4()}")
    _cursor: str = field(default="0-0", init=False)
    _initialized: bool = field(default=False, init=False)

    def _ensure_group(self) -> None:
        if self._initialized:
            return
        try:
            self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        self._initialized = True

    def _heartbeat(self, conn: Connection) -> None:
        row = (
            conn.execute(db.health.select().where(db.health.c.service == "ingestion"))
            .mappings()
            .first()
        )
        data = row["data"] if row else {}
        db.put(
            conn,
            db.health,
            "ingestion",
            {
                "data": {
                    **data,
                    "heartbeat_at": db.iso(db.utcnow()),
                    "broker_pending": self.client.xpending(self.stream, self.group)["pending"],
                }
            },
        )

    def process_message(self, message_id: str, fields: Mapping[str, str]) -> None:
        with db.transaction(self.engine) as conn:
            try:
                payload = json.loads(fields.get("payload", "null"))
            except json.JSONDecodeError:
                db.log(
                    conn,
                    "rejected",
                    broker_message_id=message_id,
                    reason="Invalid JSON",
                    raw=dict(fields),
                )
            else:
                self._ingest_payload(conn, message_id, payload)
            self._heartbeat(conn)
        self.client.xack(self.stream, self.group, message_id)

    @staticmethod
    def _ingest_payload(conn: Connection, message_id: str, payload: object) -> None:
        if isinstance(payload, dict) and "frame" in payload:
            frame = payload["frame"]
            if not isinstance(frame, list) or len(frame) > 2000:
                db.log(
                    conn,
                    "rejected",
                    reason="Invalid or oversized source frame",
                    broker_message_id=message_id,
                )
            else:
                for observation in frame:
                    ingest(conn, observation)
        else:
            ingest(conn, payload)

    def run_once(self) -> int:
        self._ensure_group()
        reclaimed = self.client.xautoclaim(
            self.stream,
            self.group,
            self.consumer,
            min_idle_time=30000,
            start_id=self._cursor,
            count=100,
        )
        self._cursor = reclaimed[0]
        messages = reclaimed[1]
        if not messages:
            batches = self.client.xreadgroup(
                self.group, self.consumer, {self.stream: ">"}, count=100, block=1000
            )
            messages = batches[0][1] if batches else []
        for message_id, fields in messages:
            self.process_message(message_id, fields)
            if self.engine.dialect.name == "sqlite":
                time.sleep(0.005)
        if not messages:
            with db.transaction(self.engine) as conn:
                self._heartbeat(conn)
        return len(messages)

    def run_forever(self, stop: Event | None = None) -> None:
        stop = stop or Event()
        while not stop.is_set():
            self.run_once()
