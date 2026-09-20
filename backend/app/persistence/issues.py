from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app import db

from .records import require_record


@dataclass(frozen=True)
class IssueQueries:
    engine: Engine

    def list_issues(self):
        with self.engine.connect() as conn:
            return list(reversed(db.rows(conn, db.issues)))

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
