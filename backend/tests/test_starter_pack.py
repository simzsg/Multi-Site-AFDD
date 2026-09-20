from collections import Counter

import pytest
from app import db, rules, schema, starter_pack
from app.evaluator import drain
from app.ingestion import ingest
from app.ontology import Registry
from app.schemas import Confirmation, RuleConfig
from app.seed import import_inventory


@pytest.fixture
def source_engine():
    engine = db.connect("sqlite:///:memory:")
    schema.upgrade(engine)
    with db.transaction(engine) as conn:
        import_inventory(conn, starter_pack.inventory())
    yield engine
    engine.dispose()


def test_supplied_inventory_and_measurement_scope(source_engine):
    with source_engine.connect() as conn:
        registry = Registry(conn)
        counts = Counter(e["kind"] for e in registry.entities.values())
        assert counts["Building"] == 3
        assert counts["Room"] == 54
        assert len(registry.entities) == 465
        assert registry.entities["building-c"]["data"]["property_type"] == "hotel"
        preview = registry.preview(RuleConfig())
        assert len(preview["matches"]) == 16
        assert len(preview["exclusions"]) == 8
        assert registry.related("meter-a-f01", "hasLocation")[0]["id"] == "building-a-plant-room"
        assert registry.related("meter-a-f01", "measuresSpace")[0]["id"] == "building-a-f01"
        spaces = registry.spaces("ahu-a-f02-east")
        assert {r["id"] for r in spaces["rooms"]} == {
            "building-a-f02-east-r01",
            "building-a-f02-east-r02",
        }
        assert (
            len(registry.preview(RuleConfig(target={"floor_ids": ["building-a-f02"]}))["matches"])
            == 2
        )


def test_source_delivery_order_and_original_ids():
    ahu_records = [item for item in starter_pack.source_schedule() if item[1] == "ahu_readings.csv"]
    assert ahu_records[-1][-1]["source_record_id"] == "src-ahu-0070-000"
    assert ahu_records[-1][-1]["observed_at"] == "2026-01-15T09:10:00Z"
    assert ahu_records[-1][0] == "2026-01-15T13:59:00Z"
    assert sum(item[-1]["source_record_id"] == "src-ahu-0100-001" for item in ahu_records) == 2


def test_blank_measurement_is_null_not_fake_normal(source_engine):
    with db.transaction(source_engine) as conn:
        registry = Registry(conn)
        row = next(
            item[-1]
            for item in starter_pack.source_schedule()
            if item[-1]["source_record_id"] == "src-ahu-0250-007"
        )
        events = list(starter_pack.point_events(registry, "ahu_readings.csv", "equipment_id", row))
        missing = next(e for e in events if e["point_id"] == "ahu-a-f04-west-sat-sp")
        assert missing["value"] is None
        assert missing["quality"] == "MISSING"
        assert missing["source"]["raw_value"] == ""
        assert ingest(conn, missing)["status"] == "accepted"
        assert ingest(conn, missing)["status"] == "duplicate"
        assert db.rows(conn, db.current)[0]["data"]["value"] is None


def test_source_deviation_windows_with_and_without_override(source_engine):
    with db.transaction(source_engine) as conn:
        for overrides in [{}, {"building-b": {"threshold": 2}}]:
            config = RuleConfig(overrides=overrides)
            version = rules.create(conn, config)
            preview = Registry(conn).preview(config)
            rules.activate(
                conn,
                version,
                Confirmation(
                    confirmed=True, preview_digest=preview["digest"], reviewer="Source test"
                ),
                source_replay_start="2026-01-15T08:00:00Z",
            )
        registry = Registry(conn)
        wanted = {"ahu-a-f02-east", "ahu-a-f03-west", "ahu-b-f01-west", "ahu-b-f04-east"}
        for _, events in starter_pack.batches(registry):
            for event in events:
                if event.get("source", {}).get("equipment_id") in wanted:
                    ingest(conn, event)
            drain(conn, force=True)
        found = db.rows(conn, db.issues)
        assert Counter(i["equipment_id"] for i in found) == {
            "ahu-a-f02-east": 2,
            "ahu-b-f01-west": 1,
        }
        for issue in found:
            is_a = issue["equipment_id"] == "ahu-a-f02-east"
            assert issue["status"] == "RECOVERED"
            assert issue["data"]["triggered_at"] == (
                "2026-01-15T10:15:00+00:00" if is_a else "2026-01-15T11:35:00+00:00"
            )
            assert issue["data"]["recovered_at"] == (
                "2026-01-15T10:21:00+00:00" if is_a else "2026-01-15T11:41:00+00:00"
            )
            assert len(issue["data"]["observations"]) == 16
