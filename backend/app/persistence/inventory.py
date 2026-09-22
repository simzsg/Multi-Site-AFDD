from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.engine import Engine

from app import db
from app.persistence.ontology import load_registry
from app.semantic import entity as semantic_entity
from app.semantic import relationship as semantic_relationship

from .records import require_record


@dataclass(frozen=True)
class InventoryQueries:
    engine: Engine

    def entities(self, kind: str | None = None):
        with self.engine.connect() as conn:
            query = db.entities.select()
            if kind:
                query = query.where(db.entities.c.kind == kind)
            query = query.order_by(db.entities.c.id)
            return [semantic_entity(dict(row)) for row in conn.execute(query).mappings()]

    def equipment(self):
        with self.engine.connect() as conn:
            query = (
                db.entities.select()
                .where(db.entities.c.kind.in_(("AHU", "IAQ_Device", "Electrical_Meter")))
                .order_by(db.entities.c.id)
            )
            return [semantic_entity(dict(row)) for row in conn.execute(query).mappings()]

    def points(self):
        return [e for e in self.entities() if "unit" in e["data"]]

    def relationships(self):
        with self.engine.connect() as conn:
            query = db.edges.select().order_by(
                db.edges.c.source, db.edges.c.relation, db.edges.c.target
            )
            return [semantic_relationship(dict(row)) for row in conn.execute(query).mappings()]

    def equipment_relationships(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            query = (
                db.edges.select()
                .where(or_(db.edges.c.source == identity, db.edges.c.target == identity))
                .order_by(db.edges.c.source, db.edges.c.relation, db.edges.c.target)
            )
            return [semantic_relationship(dict(row)) for row in conn.execute(query).mappings()]

    def spaces(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            spaces = load_registry(conn).spaces(identity)
            return {
                **spaces,
                "zones": [semantic_entity(entity) for entity in spaces["zones"]],
                "rooms": [semantic_entity(entity) for entity in spaces["rooms"]],
                "installation": [semantic_entity(entity) for entity in spaces["installation"]],
            }

    def zone_rooms(self, identity: str):
        with self.engine.connect() as conn:
            require_record(conn, db.entities, identity)
            return [
                semantic_entity(entity)
                for entity in load_registry(conn).related(identity, "hasPart")
                if entity["kind"] == "Room"
            ]
