from sqlalchemy.engine import Connection

from app import db
from app.ontology import OntologyGraph


def load_registry(conn: Connection) -> OntologyGraph:
    return OntologyGraph(db.rows(conn, db.entities), db.rows(conn, db.edges))
