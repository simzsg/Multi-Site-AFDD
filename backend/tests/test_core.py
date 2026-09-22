from datetime import timedelta

import pytest
from app import db, evaluator, rules
from app.evaluator import drain
from app.ingestion import ingest
from app.ontology import Registry
from app.schemas import Confirmation, RuleConfig

BASE = db.utcnow() - timedelta(hours=4)
EQ = "demo-a-f1-ahu1"


def event(kind, minute, value, **extra):
    return {
        "event_id": f"{kind}-{minute}",
        "point_id": f"{EQ}-{kind}",
        "device_timestamp": db.iso(BASE + timedelta(minutes=minute)),
        "value": value,
        "unit": "bool" if kind == "Run_Status" else "C",
        "quality": "GOOD",
        **extra,
    }


def frame(conn, minute, sat=20, run=1, missing=False, quality="GOOD"):
    for kind, value in [
        ("Run_Status", run),
        ("Supply_Air_Temperature_Setpoint", 16),
        ("Supply_Air_Temperature_Sensor", sat),
    ]:
        if missing and kind == "Supply_Air_Temperature_Sensor":
            continue
        ingest(conn, event(kind, minute, value, quality=quality))
    drain(conn, force=True)


def active(conn, **kwargs):
    config = RuleConfig(**kwargs)
    v = rules.create(conn, config)
    preview = Registry(conn).preview(config)
    v = rules.activate(
        conn, v, Confirmation(confirmed=True, preview_digest=preview["digest"], reviewer="test")
    )
    v["activation"]["event_time_start"] = db.iso(BASE)
    conn.execute(
        db.versions.update().where(db.versions.c.id == v["id"]).values(activation=v["activation"])
    )
    return v


def test_inventory_and_relationships(engine):
    with db.transaction(engine) as c:
        r = Registry(c)
        for kind, count in [
            ("Building", 3),
            ("Floor", 12),
            ("HVAC_Zone", 24),
            ("AHU", 24),
            ("IAQ_Device", 48),
            ("Electrical_Meter", 12),
        ]:
            assert sum(e["kind"] == kind for e in r.entities.values()) == count
        s = r.spaces(EQ)
        assert len(s["rooms"]) == 2
        assert s["installation"][0]["id"] not in {r["id"] for r in s["rooms"]}
        assert len(r.preview(RuleConfig(target={"floor_ids": ["demo-a-f1"]}))["matches"]) == 2


def test_ingestion(engine):
    with db.transaction(engine) as c:
        e = event("Run_Status", 10, 1)
        assert ingest(c, e)["status"] == "accepted"
        assert ingest(c, e)["status"] == "duplicate"
        assert ingest(c, {**e, "value": 0})["status"] == "rejected"
        assert ingest(c, event("Run_Status", 5, 0))["current_updated"] is False
        assert db.rows(c, db.current)[0]["data"]["value"] == 1
        assert len(db.rows(c, db.telemetry)) == 2
        for change in [
            {"unit": "C"},
            {"point_id": "invented"},
            {"value": "1"},
            {"value": True},
            {"quality": "UNKNOWN"},
            {"device_timestamp": "2026-01-01T00:00:00"},
            {"value": float("inf")},
        ]:
            assert ingest(c, {**event("Run_Status", 11, 1), **change})["status"] == "rejected"


def test_live_timeline_transition_is_not_reported_as_device_gap(engine):
    with db.transaction(engine) as c:
        ingest(c, event("Run_Status", 0, 1, source={"file": "fixture.csv"}))
        ingest(
            c,
            event(
                "Run_Status",
                10,
                1,
                source={"mode": "live-source", "original_event_id": "fixture-1"},
            ),
        )
        assert not [row for row in db.rows(c, db.audit) if row["action"] == "data_gap"]
        ingest(
            c,
            event(
                "Run_Status",
                13,
                1,
                source={"mode": "live-source", "original_event_id": "fixture-2"},
            ),
        )
        assert len([row for row in db.rows(c, db.audit) if row["action"] == "data_gap"]) == 1


def test_boundary_recovery_recurrence_and_evidence(engine):
    with db.transaction(engine) as c:
        v = active(c)
        for minute in range(15):
            frame(c, minute)
        assert not db.rows(c, db.issues)
        frame(c, 15)
        first = db.rows(c, db.issues)[0]
        assert len(first["data"]["observations"]) == 16
        frame(c, 16)
        assert len(db.rows(c, db.issues)) == 1
        frame(c, 17, sat=18)
        assert db.rows(c, db.issues)[0]["status"] == "RECOVERED"
        for minute in range(18, 34):
            frame(c, minute)
        assert len(db.rows(c, db.issues)) == 2
        rules.create(c, RuleConfig(logic={"threshold": 5}), v["rule_id"])
        assert db.rows(c, db.issues)[0]["data"]["config"]["logic"]["threshold"] == 3


@pytest.mark.parametrize(
    "sat,run,missing,quality",
    [(19, 1, False, "GOOD"), (20, 0, False, "GOOD"), (20, 1, True, "GOOD"), (20, 1, False, "BAD")],
)
def test_no_misleading_issue(engine, sat, run, missing, quality):
    with db.transaction(engine) as c:
        active(c)
        for minute in range(20):
            frame(c, minute, sat, run, missing, quality)
        assert not db.rows(c, db.issues)


def test_gap_resets_interval(engine):
    with db.transaction(engine) as c:
        active(c)
        for minute in list(range(10)) + list(range(14, 25)):
            frame(c, minute)
        assert not db.rows(c, db.issues)


def test_override_and_missing_point(engine):
    with db.transaction(engine) as c:
        active(c, overrides={"demo-a": {"threshold": 5, "duration_minutes": 2}})
        for minute in range(16):
            frame(c, minute)
        assert not db.rows(c, db.issues)
        for minute in range(16, 19):
            frame(c, minute, sat=22)
        assert db.rows(c, db.issues)[0]["data"]["threshold"] == 5
        c.execute(db.edges.delete().where(db.edges.c.target == f"{EQ}-Run_Status"))
        preview = Registry(c).preview(RuleConfig())
        assert any(
            e["equipment_id"] == EQ and "Run_Status" in e["missing_points"]
            for e in preview["exclusions"]
        )


def test_human_confirmation_and_changed_ontology(engine):
    with db.transaction(engine) as c:
        v = rules.create(c, RuleConfig())
        with pytest.raises(ValueError, match="Preview changed"):
            rules.activate(
                c, v, Confirmation(confirmed=True, preview_digest="stale", reviewer="test")
            )
        assert db.rows(c, db.versions)[0]["status"] == "DRAFT"


def test_bad_input_does_not_recover_active_issue(engine):
    with db.transaction(engine) as c:
        active(c)
        for minute in range(16):
            frame(c, minute)
        frame(c, 16, quality="BAD")
        assert db.rows(c, db.issues)[0]["status"] == "ACTIVE"
        assert db.rows(c, db.states)[0]["data"]["status"] == "INSUFFICIENT_DATA"
        frame(c, 17, run=0)
        assert db.rows(c, db.issues)[0]["status"] == "RECOVERED"
        assert db.rows(c, db.issues)[0]["data"]["recovery_reason"] == "OFF"


def test_older_observations_do_not_rewrite_issue(engine):
    with db.transaction(engine) as c:
        active(c)
        for minute in range(16):
            frame(c, minute)
        evidence = db.rows(c, db.issues)[0]["data"]
        frame(c, 0.5, sat=16)
        assert db.rows(c, db.issues)[0]["data"] == evidence
        assert db.rows(c, db.issues)[0]["status"] == "ACTIVE"


def test_disable_stops_occurrence_without_false_recovery(engine):
    with db.transaction(engine) as c:
        version = active(c)
        for minute in range(16):
            frame(c, minute)
        rules.stop(c, version["id"])
        issue = db.rows(c, db.issues)[0]
        assert issue["status"] == "STOPPED"
        assert issue["data"]["recovered_at"] is None
        assert not db.rows(c, db.states)


def test_wrong_service_relationship_and_stale_confirmation(engine):
    with db.transaction(engine) as c:
        config = RuleConfig()
        version = rules.create(c, config)
        preview = Registry(c).preview(config)
        c.execute(db.edges.delete().where(db.edges.c.source == EQ, db.edges.c.relation == "feeds"))
        c.execute(db.edges.insert().values(source=EQ, relation="feeds", target="demo-a-plant"))
        new_preview = Registry(c).preview(config)
        assert EQ not in [m["equipment_id"] for m in new_preview["matches"]]
        with pytest.raises(ValueError, match="Preview changed"):
            rules.activate(
                c,
                version,
                Confirmation(confirmed=True, preview_digest=preview["digest"], reviewer="test"),
            )


def test_equal_timestamp_point_order_independent(engine):

    with db.transaction(engine) as c:
        active(c, logic={"duration_minutes": 1})
        for minute in range(2):
            for kind, value in [
                ("Supply_Air_Temperature_Sensor", 21),
                ("Supply_Air_Temperature_Setpoint", 16),
                ("Run_Status", 1),
            ]:
                ingest(c, event(kind, minute, value))
            drain(c, force=True)
        assert len(db.rows(c, db.issues)) == 1
        assert db.rows(c, db.issues)[0]["data"]["rule_version"] == 1


def test_non_default_comparison_logic(engine):
    with db.transaction(engine) as c:
        active(
            c,
            logic={
                "left": "Return_Air_Temperature_Sensor",
                "operator": "DIFF_LT",
                "threshold": 2,
                "duration_minutes": 1,
                "severity": "WARNING",
            },
        )
        for minute in range(2):
            ingest(c, event("Return_Air_Temperature_Sensor", minute, 17))
            frame(c, minute, sat=16)
        issue = db.rows(c, db.issues)[0]
        assert issue["data"]["severity"] == "WARNING"
        assert issue["data"]["calculated_difference"] == 1


def test_evaluator_limits_each_outbox_transaction(engine, monkeypatch):
    monkeypatch.setattr(evaluator, "OUTBOX_BATCH_SIZE", 2)
    with db.transaction(engine) as conn:
        for minute in range(3):
            ingest(conn, event("Run_Status", minute, 1))
        assert drain(conn, force=True) == 2
        assert drain(conn, force=True) == 1
        health = (
            conn.execute(db.health.select().where(db.health.c.service == "evaluator"))
            .mappings()
            .one()
        )
        assert health["data"]["pending"] == 0
