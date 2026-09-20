from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.engine import Engine

from app import db

from .records import require_record


@dataclass(frozen=True)
class TelemetryQueries:
    engine: Engine

    def current(self):
        with self.engine.connect() as conn:
            return {r["point_id"]: r["data"] for r in db.rows(conn, db.current)}

    def latest(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            row = (
                conn.execute(db.current.select().where(db.current.c.point_id == identity))
                .mappings()
                .first()
            )
            return row["data"] if row else {"status": "MISSING"}

    def history(
        self,
        identity: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            query = db.telemetry.select().where(db.telemetry.c.point_id == identity)
            if start:
                query = query.where(db.telemetry.c.device_timestamp >= start)
            if end:
                query = query.where(db.telemetry.c.device_timestamp <= end)
            return list(
                reversed(
                    [
                        dict(r)
                        for r in conn.execute(
                            query.order_by(db.telemetry.c.device_timestamp.desc()).limit(limit)
                        ).mappings()
                    ]
                )
            )
