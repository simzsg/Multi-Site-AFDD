import json
import math
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.pool import StaticPool

from .config import Settings

metadata = MetaData()
entities = Table(
    "entities",
    metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, index=True),
    Column("label", String),
    Column("data", JSON),
)
edges = Table(
    "edges",
    metadata,
    Column("source", String, primary_key=True),
    Column("relation", String, primary_key=True),
    Column("target", String, primary_key=True),
)
Index("ix_edges_source_relation", edges.c.source, edges.c.relation)
Index("ix_edges_target_relation", edges.c.target, edges.c.relation)
receipts = Table(
    "event_receipts",
    metadata,
    Column("event_id", String, primary_key=True),
    Column("digest", String),
    Column("received_at", DateTime(timezone=True)),
)
telemetry = Table(
    "telemetry",
    metadata,
    Column("device_timestamp", DateTime(timezone=True), primary_key=True),
    Column("event_id", String, primary_key=True),
    Column("point_id", String, index=True),
    Column("value", Float),
    Column("unit", String),
    Column("quality", String),
    Column("source", JSON),
    Column("received_at", DateTime(timezone=True)),
)
Index(
    "uq_telemetry_point_time",
    telemetry.c.point_id,
    telemetry.c.device_timestamp,
    unique=True,
)

current = Table(
    "current_values", metadata, Column("point_id", String, primary_key=True), Column("data", JSON)
)
outbox = Table(
    "evaluation_outbox",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("data", JSON),
    Column("done", Boolean, default=False),
)
Index("ix_evaluation_outbox_pending_id", outbox.c.done, outbox.c.id)
versions = Table(
    "rule_versions",
    metadata,
    Column("id", String, primary_key=True),
    Column("rule_id", String, index=True),
    Column("version", Integer),
    Column("config", JSON),
    Column("status", String),
    Column("created_at", String),
    Column("activation", JSON),
)
Index("ix_rule_versions_status", versions.c.status)
states = Table(
    "evaluation_states", metadata, Column("id", String, primary_key=True), Column("data", JSON)
)
issues = Table(
    "issues",
    metadata,
    Column("id", String, primary_key=True),
    Column("version_id", String, index=True),
    Column("equipment_id", String),
    Column("status", String),
    Column("data", JSON),
)
Index("ix_issues_status_equipment", issues.c.status, issues.c.equipment_id)
audit = Table(
    "audit_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("at", String),
    Column("action", String),
    Column("data", JSON),
)
Index("ix_audit_events_action_id", audit.c.action, audit.c.id)
ai_requests = Table(
    "ai_requests", metadata, Column("id", String, primary_key=True), Column("data", JSON)
)
health = Table(
    "service_health", metadata, Column("service", String, primary_key=True), Column("data", JSON)
)


def utcnow():
    return datetime.now(timezone.utc)


def iso(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def connect(url=None):
    url = url or Settings.from_env().database_url
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


@contextmanager
def transaction(engine):
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql("BEGIN IMMEDIATE")
        yield conn


def rows(conn, table):
    return [dict(r) for r in conn.execute(table.select()).mappings()]


def put(conn, table, key, value):
    primary_key = list(table.primary_key)
    if len(primary_key) != 1:
        raise ValueError(f"Atomic put requires one primary key column: {table.name}")
    column = primary_key[0]
    values = {column.name: key, **value}
    if conn.dialect.name == "postgresql":
        statement = pg_insert(table).values(**values)
    elif conn.dialect.name == "sqlite":
        statement = sqlite_insert(table).values(**values)
    else:
        updated = conn.execute(table.update().where(column == key).values(**value))
        if not updated.rowcount:
            conn.execute(table.insert().values(**values))
        return
    conn.execute(
        statement.on_conflict_do_update(
            index_elements=[column],
            set_={name: statement.excluded[name] for name in value},
        )
    )


def insert_once(conn, table, values, conflict_columns):
    if conn.dialect.name == "postgresql":
        statement = pg_insert(table).values(**values)
    elif conn.dialect.name == "sqlite":
        statement = sqlite_insert(table).values(**values)
    else:
        raise RuntimeError(f"Unsupported database dialect: {conn.dialect.name}")
    result = conn.execute(
        statement.on_conflict_do_nothing(index_elements=list(conflict_columns)).returning(
            conflict_columns[0]
        )
    )
    return result.scalar_one_or_none() is not None


def lock(conn, scope, identity):
    if conn.dialect.name == "postgresql":
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:identity, 0))"),
            {"identity": f"{scope}:{identity}"},
        )


def try_lock(conn, scope):
    if conn.dialect.name != "postgresql":
        return True
    return bool(
        conn.execute(
            text("SELECT pg_try_advisory_xact_lock(hashtextextended(:scope, 0))"),
            {"scope": scope},
        ).scalar()
    )


def log(conn, action, **data):
    def safe(value):
        if isinstance(value, float) and not math.isfinite(value):
            return str(value)
        if isinstance(value, dict):
            return {k: safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [safe(v) for v in value]
        return value

    data = safe(data)
    payload = {"at": iso(utcnow()), "action": action, "data": data}
    conn.execute(audit.insert().values(**payload))
    print(json.dumps({"service": os.getenv("SERVICE_NAME", "afdd"), **payload}), flush=True)
