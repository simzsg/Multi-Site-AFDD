from app import db
from app.schema import HEAD_REVISION, require_current, upgrade
from sqlalchemy import inspect, text


def test_fresh_database_upgrades_to_versioned_schema(tmp_path):
    engine = db.connect(f"sqlite:///{tmp_path / 'fresh.db'}")
    try:
        upgrade(engine)
        upgrade(engine)
        assert require_current(engine) == HEAD_REVISION
        assert set(inspect(engine).get_table_names()) == {
            *db.metadata.tables,
            "alembic_version",
        }
        assert {
            "ix_edges_source_relation",
            "ix_edges_target_relation",
        }.issubset({index["name"] for index in inspect(engine).get_indexes("edges")})
        telemetry_indexes = {
            index["name"]: index for index in inspect(engine).get_indexes("telemetry")
        }
        assert telemetry_indexes["uq_telemetry_point_time"]["unique"]
    finally:
        engine.dispose()


def test_existing_unversioned_schema_is_validated_stamped_and_preserved(tmp_path):
    engine = db.connect(f"sqlite:///{tmp_path / 'legacy.db'}")
    try:
        db.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(
                db.entities.insert().values(
                    id="existing", kind="Building", label="Existing", data={}
                )
            )
        upgrade(engine)
        assert require_current(engine) == HEAD_REVISION
        with engine.connect() as conn:
            assert conn.execute(
                text("select label from entities where id='existing'")
            ).scalar() == ("Existing")
    finally:
        engine.dispose()


def test_unversioned_v2_schema_is_detected_before_latest_migration(tmp_path):
    engine = db.connect(f"sqlite:///{tmp_path / 'v2.db'}")
    try:
        db.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(text("DROP INDEX uq_telemetry_point_time"))
            conn.execute(
                text(
                    "CREATE INDEX ix_telemetry_point_time ON telemetry (point_id, device_timestamp)"
                )
            )
        upgrade(engine)
        indexes = {index["name"] for index in inspect(engine).get_indexes("telemetry")}
        assert require_current(engine) == HEAD_REVISION
        assert "uq_telemetry_point_time" in indexes
        assert "ix_telemetry_point_time" not in indexes
    finally:
        engine.dispose()


def test_partial_unversioned_schema_is_rejected_instead_of_blindly_stamped(tmp_path):
    engine = db.connect(f"sqlite:///{tmp_path / 'partial.db'}")
    try:
        db.entities.create(engine)
        try:
            upgrade(engine)
        except RuntimeError as exc:
            assert "Unversioned database does not match" in str(exc)
        else:
            raise AssertionError("Partial schemas must not be stamped")
        assert "alembic_version" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
