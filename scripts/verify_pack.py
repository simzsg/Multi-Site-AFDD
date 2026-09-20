from app import db
from app.ontology import Registry
from app.schemas import RuleConfig
from sqlalchemy import func, select

with db.connect().connect() as conn:
    registry = Registry(conn)
    assert len(registry.entities) == 465
    assert len(registry.preview(RuleConfig())["matches"]) == 16
    assert conn.execute(select(func.count()).select_from(db.telemetry)).scalar() == 103655
    actions = dict(
        conn.execute(select(db.audit.c.action, func.count()).group_by(db.audit.c.action)).all()
    )
    assert {k: actions[k] for k in ["duplicate", "late", "incomplete", "rejected", "data_gap"]} == {
        "duplicate": 5,
        "late": 5,
        "incomplete": 6,
        "rejected": 1,
        "data_gap": 10,
    }
    issues = db.rows(conn, db.issues)
    assert len(issues) == 2
    expected = {"ahu-a-f02-east": ("10:15", "10:21", 3), "ahu-b-f01-west": ("11:35", "11:41", 2)}
    for issue in issues:
        trigger, recovery, threshold = expected[issue["equipment_id"]]
        evidence = issue["data"]
        assert issue["status"] == "RECOVERED"
        assert evidence["triggered_at"][11:16] == trigger
        assert evidence["recovered_at"][11:16] == recovery
        assert evidence["threshold"] == threshold
        assert len(evidence["observations"]) == 16
        assert len(evidence["affected"]["rooms"]) == 2
        assert evidence["observations"][0]["observations"]["Supply_Air_Temperature_Sensor"][
            "source"
        ]["source_record_id"]
    latest = (
        conn.execute(db.current.select().where(db.current.c.point_id == "ahu-a-f01-east-sat"))
        .mappings()
        .one()
    )
    assert latest["data"]["device_timestamp"].startswith("2026-01-15T13:59")
print(
    "PASS: entire supplied pack, exact issue/recovery windows, override, provenance, duplicate/late/missing/rejection counts"
)
