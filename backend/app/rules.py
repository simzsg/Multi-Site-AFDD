from uuid import uuid4

from sqlalchemy import func, select

from . import db
from .ontology import Registry
from .schemas import RuleConfig


def create(conn, config: RuleConfig, rule_id=None):
    validation = Registry(conn).validate(config)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))
    rule_id = rule_id or str(uuid4())
    db.lock(conn, "rule", rule_id)
    previous_version = conn.execute(
        select(func.max(db.versions.c.version)).where(db.versions.c.rule_id == rule_id)
    ).scalar()
    version = {
        "id": str(uuid4()),
        "rule_id": rule_id,
        "version": (previous_version or 0) + 1,
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
    active_issues = list(
        conn.execute(
            db.issues.select().where(
                db.issues.c.version_id == version_id, db.issues.c.status == "ACTIVE"
            )
        ).mappings()
    )
    stopped_at = db.iso(db.utcnow())
    for issue in active_issues:
        conn.execute(
            db.issues.update()
            .where(db.issues.c.id == issue["id"])
            .values(
                status="STOPPED",
                data={
                    **issue["data"],
                    "stopped_at": stopped_at,
                    "stop_reason": reason,
                },
            )
        )
    conn.execute(db.states.delete().where(db.states.c.id.like(f"{version_id}:%")))
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
    active_versions = list(
        conn.execute(
            db.versions.select().where(
                db.versions.c.rule_id == version["rule_id"], db.versions.c.status == "ACTIVE"
            )
        ).mappings()
    )
    for other in active_versions:
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
