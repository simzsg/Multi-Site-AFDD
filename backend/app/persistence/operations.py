from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine

from app import db
from app.config import Settings


@dataclass(frozen=True)
class OperationsQueries:
    engine: Engine
    settings: Settings

    def health(self):
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": self.engine.dialect.name,
            "source_replay_start": self.settings.source_replay_start,
            "model_configured": self.settings.model_configured,
        }

    def pipeline(self):
        with self.engine.connect() as conn:
            services = {r["service"]: r["data"] for r in db.rows(conn, db.health)}
            services["pending_evaluations"] = conn.execute(
                select(func.count()).select_from(db.outbox).where(db.outbox.c.done.is_(False))
            ).scalar()
            actions = ("rejected", "duplicate", "late", "incomplete", "data_gap")
            counts = dict(
                conn.execute(
                    select(db.audit.c.action, func.count())
                    .where(db.audit.c.action.in_(actions))
                    .group_by(db.audit.c.action)
                ).all()
            )
            for action in actions:
                services[action if action != "duplicate" else "duplicates"] = counts.get(action, 0)
            return services

    def ingestion_health(self):
        return self.pipeline().get("ingestion", {"status": "not_started"})

    def evaluator_health(self):
        return self.pipeline().get("evaluator", {"status": "not_started"})

    def audit(self, limit: int = 100, action: str | None = None):
        with self.engine.connect() as conn:
            query = db.audit.select()
            if action:
                query = query.where(db.audit.c.action == action)
            return [
                dict(r)
                for r in conn.execute(query.order_by(db.audit.c.id.desc()).limit(limit)).mappings()
            ]
