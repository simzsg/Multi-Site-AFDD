from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app import db, rules
from app.ontology import Registry
from app.persistence.records import require_record
from app.schemas import Confirmation, RuleConfig


@dataclass(frozen=True)
class RuleService:
    engine: Engine
    source_replay_start: str | None = None

    def list_rules(self):
        with self.engine.connect() as conn:
            query = db.versions.select().order_by(
                db.versions.c.created_at, db.versions.c.rule_id, db.versions.c.version
            )
            return [dict(row) for row in conn.execute(query).mappings()]

    def create_rule(self, config: RuleConfig):
        with db.transaction(self.engine) as conn:
            return rules.create(conn, config)

    def rule(self, identity: str):
        with self.engine.connect() as conn:
            return require_record(conn, db.versions, identity)

    def validate(self, identity: str):
        with self.engine.connect() as conn:
            return Registry(conn).validate(
                RuleConfig.model_validate(require_record(conn, db.versions, identity)["config"])
            )

    def preview(self, identity: str):
        with self.engine.connect() as conn:
            return Registry(conn).preview(
                RuleConfig.model_validate(require_record(conn, db.versions, identity)["config"])
            )

    def activate(self, identity: str, confirmation: Confirmation):
        with db.transaction(self.engine) as conn:
            result = rules.activate(
                conn,
                require_record(conn, db.versions, identity),
                confirmation,
                source_replay_start=self.source_replay_start,
            )
            requests = list(
                conn.execute(
                    db.ai_requests.select().where(
                        db.ai_requests.c.data["draft"]["id"].as_string() == identity
                    )
                ).mappings()
            )
            for request in requests:
                data = {
                    **request["data"],
                    "state": "ACTIVATED",
                    "human_confirmation": confirmation.model_dump(),
                    "activation_result": result,
                }
                db.put(conn, db.ai_requests, request["id"], {"data": data})
            return result

    def disable(self, identity: str):
        with db.transaction(self.engine) as conn:
            require_record(conn, db.versions, identity)
            rules.stop(conn, identity)
            return {"status": "DISABLED"}

    def adjust(self, identity: str, config: RuleConfig):
        with db.transaction(self.engine) as conn:
            old = require_record(conn, db.versions, identity)
            return rules.create(conn, config, old["rule_id"])

    def rule_versions(self, identity: str):
        with self.engine.connect() as conn:
            old = require_record(conn, db.versions, identity)
            query = (
                db.versions.select()
                .where(db.versions.c.rule_id == old["rule_id"])
                .order_by(db.versions.c.version)
            )
            return [dict(row) for row in conn.execute(query).mappings()]
