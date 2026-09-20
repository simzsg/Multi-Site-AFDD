from uuid import uuid4

from . import db
from .ontology import Registry
from .schemas import RuleConfig


def create(conn, config: RuleConfig, rule_id=None):
    validation = Registry(conn).validate(config)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))
    rule_id = rule_id or str(uuid4())
    db.lock(conn, "rule", rule_id)
    previous = [r for r in db.rows(conn, db.versions) if r["rule_id"] == rule_id]
    version = {
        "id": str(uuid4()),
        "rule_id": rule_id,
        "version": max([r["version"] for r in previous], default=0) + 1,
        "config": config.model_dump(),
        "status": "DRAFT",
        "created_at": db.iso(db.utcnow()),
        "activation": None,
    }
    conn.execute(db.versions.insert().values(**version))
    db.log(conn, "rule_drafted", rule_id=rule_id, rule_version=version["id"])
    return version


def stop(conn, version_id, reason="DISABLED"):
    conn.execute(
        db.versions.update().where(db.versions.c.id == version_id).values(status="DISABLED")
    )
    for issue in db.rows(conn, db.issues):
        if issue["version_id"] == version_id and issue["status"] == "ACTIVE":
            conn.execute(
                db.issues.update()
                .where(db.issues.c.id == issue["id"])
                .values(
                    status="STOPPED",
                    data={
                        **issue["data"],
                        "stopped_at": db.iso(db.utcnow()),
                        "stop_reason": reason,
                    },
                )
            )
    for state in db.rows(conn, db.states):
        if state["id"].startswith(version_id + ":"):
            conn.execute(db.states.delete().where(db.states.c.id == state["id"]))
    db.log(conn, "rule_disabled", rule_version=version_id, reason=reason)


def activate(conn, version, confirmation, source_replay_start=None):
    db.lock(conn, "rule", version["rule_id"])
    version = (
        conn.execute(db.versions.select().where(db.versions.c.id == version["id"])).mappings().one()
    )
    if version["status"] != "DRAFT":
        raise ValueError("Only a draft can be activated; adjust to create a new version")
    registry = Registry(conn)
    config = RuleConfig.model_validate(version["config"])
    validation = registry.validate(config)
    if not validation["valid"]:
        raise ValueError("Ontology changed: " + "; ".join(validation["errors"]))
    preview = registry.preview(config)
    if not preview["matches"]:
        raise ValueError("No matched equipment")
    if confirmation.preview_digest != preview["digest"]:
        raise ValueError("Preview changed; review the current targets before confirming")
    for other in db.rows(conn, db.versions):
        if other["rule_id"] == version["rule_id"] and other["status"] == "ACTIVE":
            stop(conn, other["id"], "SUPERSEDED")
    replay_start = source_replay_start
    if replay_start:
        replay_start = db.iso(db.stamp(replay_start))
    activation = {
        "reviewer": confirmation.reviewer,
        "confirmed": True,
        "preview_digest": preview["digest"],
        "confirmed_at": db.iso(db.utcnow()),
        "event_time_start": replay_start or db.iso(db.utcnow()),
        "clock_mode": "SOURCE_REPLAY" if replay_start else "LIVE",
    }
    conn.execute(
        db.versions.update()
        .where(db.versions.c.id == version["id"])
        .values(status="ACTIVE", activation=activation)
    )
    db.log(conn, "human_confirmed_activation", rule_version=version["id"], **activation)
    return {**version, "status": "ACTIVE", "activation": activation}
