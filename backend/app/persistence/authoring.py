from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app import db

from .records import require_record


@dataclass(frozen=True)
class AuthoringQueries:
    engine: Engine

    def ai_history(self):
        with self.engine.connect() as conn:
            return db.rows(conn, db.ai_requests)

    def ai_request(self, identity: str):
        with self.engine.connect() as conn:
            return require_record(conn, db.ai_requests, identity)
