from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app import db
from app.ontology import Registry

from .records import require_record


@dataclass(frozen=True)
class InventoryQueries:
    engine: Engine

    def entities(self, kind: str | None = None):
        with self.engine.connect() as conn:
            return [e for e in db.rows(conn, db.entities) if not kind or e["kind"] == kind]

    def equipment(self):
        return [
            e for e in self.entities() if e["kind"] in {"AHU", "IAQ_Device", "Electrical_Meter"}
        ]

    def points(self):
        return [e for e in self.entities() if "unit" in e["data"]]

    def relationships(self):
        with self.engine.connect() as conn:
            return db.rows(conn, db.edges)

    def equipment_relationships(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            return [e for e in db.rows(conn, db.edges) if identity in (e["source"], e["target"])]

    def spaces(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            return Registry(conn).spaces(identity)

    def zone_rooms(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            return [r for r in Registry(conn).related(identity, "hasPart") if r["kind"] == "Room"]
