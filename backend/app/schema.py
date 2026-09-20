from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

from . import db

BASELINE_REVISION = "20260920_0001"
HEAD_REVISION = "20260920_0002"
BASELINE_INDEXES = {
    "ix_entities_kind",
    "ix_telemetry_point_id",
    "ix_telemetry_point_time",
    "ix_evaluation_outbox_done",
    "ix_rule_versions_rule_id",
    "ix_issues_version_id",
}


def _config(connection: Connection) -> Config:
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    config.attributes["connection"] = connection
    return config


def _revision(connection: Connection) -> str | None:
    return MigrationContext.configure(connection).get_current_revision()


def _validate_unversioned_schema(connection: Connection) -> str:
    inspector = inspect(connection)
    actual_tables = set(inspector.get_table_names())
    expected_tables = set(db.metadata.tables)
    if actual_tables != expected_tables:
        raise RuntimeError(
            "Unversioned database does not match the baseline schema: "
            f"expected={sorted(expected_tables)}, actual={sorted(actual_tables)}"
        )
    for name, table in db.metadata.tables.items():
        actual_columns = {column["name"]: column for column in inspector.get_columns(name)}
        expected_columns = {column.name: column for column in table.columns}
        if set(actual_columns) != set(expected_columns):
            raise RuntimeError(f"Unversioned table {name} has unexpected columns")
        actual_primary_key = set(inspector.get_pk_constraint(name)["constrained_columns"])
        expected_primary_key = {column.name for column in table.primary_key.columns}
        if actual_primary_key != expected_primary_key:
            raise RuntimeError(f"Unversioned table {name} has an unexpected primary key")
    actual_indexes = {
        index["name"]
        for table in expected_tables
        for index in inspector.get_indexes(table)
        if index["name"]
    }
    current_indexes = {
        index.name for table in db.metadata.tables.values() for index in table.indexes if index.name
    }
    if not (BASELINE_INDEXES.issubset(actual_indexes) or current_indexes.issubset(actual_indexes)):
        raise RuntimeError("Unversioned database is missing baseline indexes")
    if connection.dialect.name == "postgresql":
        extension = connection.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
        ).scalar()
        hypertable = connection.execute(
            text(
                "SELECT 1 FROM timescaledb_information.hypertables "
                "WHERE hypertable_name = 'telemetry'"
            )
        ).scalar()
        if not extension or not hypertable:
            raise RuntimeError("Unversioned PostgreSQL schema is missing its Timescale hypertable")
    return HEAD_REVISION if current_indexes.issubset(actual_indexes) else BASELINE_REVISION


def upgrade(engine: Engine) -> str:
    with engine.connect() as connection:
        revision = _revision(connection)
        tables = set(inspect(connection).get_table_names())
        if revision is None and tables:
            unversioned_revision = _validate_unversioned_schema(connection)
            command.stamp(_config(connection), unversioned_revision)
            connection.commit()
        command.upgrade(_config(connection), "head")
        connection.commit()
    return require_current(engine)


def reset(engine: Engine) -> str:
    with engine.connect() as connection:
        command.downgrade(_config(connection), "base")
        command.upgrade(_config(connection), "head")
        connection.commit()
    return require_current(engine)


def require_current(engine: Engine) -> str:
    with engine.connect() as connection:
        current = _revision(connection)
        head = ScriptDirectory.from_config(_config(connection)).get_current_head()
    if current != head:
        raise RuntimeError(f"Database revision is {current or 'unversioned'}; expected {head}")
    return current
