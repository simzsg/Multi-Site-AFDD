from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app import db

from .records import require_record


@dataclass(frozen=True)
class IssueQueries:
    engine: Engine

    def list_issues(
        self,
        status: str | None = None,
        equipment_id: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ):
        with self.engine.connect() as conn:
            query = db.issues.select()
            if status:
                query = query.where(db.issues.c.status == status)
            if equipment_id:
                query = query.where(db.issues.c.equipment_id == equipment_id)
            query = (
                query.order_by(
                    db.issues.c.data["created_at"].as_string().desc(), db.issues.c.id.desc()
                )
                .limit(limit)
                .offset(offset)
            )
            return [dict(row) for row in conn.execute(query).mappings()]

    def issue(self, identity: str):
        with self.engine.connect() as conn:
            return require_record(conn, db.issues, identity)

    def evidence(self, identity: str):
        return self.issue(identity)["data"]

    def affected(self, identity: str):
        return self.issue(identity)["data"]["affected"]

    def evaluation_states(self):
        with self.engine.connect() as conn:
            return db.rows(conn, db.states)
