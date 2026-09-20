import json
from dataclasses import dataclass
from threading import Event

from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from app import db
from app.evaluator import drain


@dataclass(frozen=True)
class EvaluationWorker:
    engine: Engine

    def run_once(self) -> int:
        try:
            with db.transaction(self.engine) as conn:
                return drain(conn)
        except OperationalError as exc:
            if self.engine.dialect.name != "sqlite" or "database is locked" not in str(exc):
                raise
            print(
                json.dumps(
                    {
                        "service": "evaluator",
                        "action": "database_busy_retry",
                        "at": db.iso(db.utcnow()),
                    }
                ),
                flush=True,
            )
            return 0

    def run_forever(self, stop: Event | None = None) -> None:
        stop = stop or Event()
        while not stop.is_set():
            self.run_once()
            stop.wait(1)
