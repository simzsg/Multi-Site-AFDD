from collections import defaultdict
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func, select

from . import db
from .persistence.ontology import load_registry
from .schemas import RuleConfig

OUTBOX_BATCH_SIZE = 5000


def compare(left, right, logic):
    difference = left - right
    if logic["operator"] == "ABS_DIFF_GT":
        difference = abs(difference)
    fault = (
        difference < logic["threshold"]
        if logic["operator"] == "DIFF_LT"
        else difference > logic["threshold"]
    )
    return difference, fault


def latest_observations(conn, point_ids, at):
    if not point_ids:
        return {}
    rank = (
        func.row_number()
        .over(
            partition_by=db.telemetry.c.point_id,
            order_by=db.telemetry.c.device_timestamp.desc(),
        )
        .label("latest_rank")
    )
    ranked = (
        select(*db.telemetry.c, rank)
        .where(
            db.telemetry.c.point_id.in_(point_ids),
            db.telemetry.c.device_timestamp <= at,
        )
        .subquery()
    )
    observations = {}
    for row in conn.execute(select(ranked).where(ranked.c.latest_rank == 1)).mappings():
        item = dict(row)
        item.pop("latest_rank")
        item["device_timestamp"] = db.iso(item["device_timestamp"])
        item["received_at"] = db.iso(item["received_at"])
        observations[item["point_id"]] = item
    return observations


def evaluate_frame(conn, version, match, at, observations):
    key = f"{version['id']}:{match['equipment_id']}"
    row = conn.execute(db.states.select().where(db.states.c.id == key)).mappings().first()
    state = (
        dict(row["data"])
        if row
        else {"status": "NORMAL", "since": None, "last_at": None, "samples": [], "issue_id": None}
    )
    if state["last_at"] and db.stamp(state["last_at"]) >= at:
        return
    logic = match["effective"]
    fresh = timedelta(seconds=logic["freshness_seconds"])
    gap = state["last_at"] and at - db.stamp(state["last_at"]) > fresh
    state["last_at"] = db.iso(at)
    inputs = {kind: observations.get(point_id) for kind, point_id in match["points"].items()}
    sufficient = all(
        v
        and v["quality"] == "GOOD"
        and timedelta(0) <= at - db.stamp(v["device_timestamp"]) <= fresh
        for v in inputs.values()
    )
    if gap:
        state.update(since=None, samples=[])
    issue_id = state.get("issue_id")
    if not sufficient:
        state.update(status="INSUFFICIENT_DATA", since=None, samples=[])
    else:
        run = inputs[logic["operating_point"]]["value"] == logic["operating_equals"]
        difference, fault = compare(
            inputs[logic["left"]]["value"], inputs[logic["right"]]["value"], logic
        )
        if not run or not fault:
            if issue_id:
                issue = (
                    conn.execute(db.issues.select().where(db.issues.c.id == issue_id))
                    .mappings()
                    .one()
                )
                data = {
                    **issue["data"],
                    "recovered_at": db.iso(at),
                    "recovery_reason": "NORMAL" if run else "OFF",
                    "recovery_observations": inputs,
                }
                conn.execute(
                    db.issues.update()
                    .where(db.issues.c.id == issue_id)
                    .values(status="RECOVERED", data=data)
                )
                db.log(conn, "issue_recovered", issue_id=issue_id, rule_version=version["id"])
            state.update(status="NORMAL", since=None, samples=[], issue_id=None)
        elif issue_id:
            state["status"] = "ACTIVE"
        else:
            state["since"] = state["since"] or db.iso(at)
            state["status"] = "QUALIFYING"
            state["samples"].append(
                {"at": db.iso(at), "observations": inputs, "difference": difference}
            )
            if (at - db.stamp(state["since"])).total_seconds() >= logic["duration_minutes"] * 60:
                issue_id = str(uuid4())
                data = {
                    "rule_id": version["rule_id"],
                    "rule_version": version["version"],
                    "config": version["config"],
                    "effective": logic,
                    "threshold": logic["threshold"],
                    "severity": logic["severity"],
                    "trigger_interval": {"start": state["since"], "end": db.iso(at)},
                    "triggered_at": db.iso(at),
                    "created_at": db.iso(db.utcnow()),
                    "observations": list(state["samples"]),
                    "calculated_difference": difference,
                    "data_quality": "GOOD",
                    "affected": match["affected"],
                    "paths": match["paths"],
                    "recovered_at": None,
                }
                conn.execute(
                    db.issues.insert().values(
                        id=issue_id,
                        version_id=version["id"],
                        equipment_id=match["equipment_id"],
                        status="ACTIVE",
                        data=data,
                    )
                )
                db.log(
                    conn,
                    "issue_triggered",
                    issue_id=issue_id,
                    rule_id=version["rule_id"],
                    rule_version=version["id"],
                    equipment_id=match["equipment_id"],
                )
                state.update(status="ACTIVE", issue_id=issue_id, samples=[])
    db.put(conn, db.states, key, {"data": state})


def drain(conn, force=False):
    if not db.try_lock(conn, "evaluation_drain"):
        return 0
    registry = load_registry(conn)
    pending_count = conn.execute(
        select(func.count()).select_from(db.outbox).where(db.outbox.c.done.is_(False))
    ).scalar_one()
    pending = [
        dict(r)
        for r in conn.execute(
            db.outbox.select()
            .where(db.outbox.c.done.is_(False))
            .order_by(db.outbox.c.id)
            .limit(OUTBOX_BATCH_SIZE)
        ).mappings()
    ]
    if not pending:
        db.put(
            conn,
            db.health,
            "evaluator",
            {"data": {"last_evaluated_at": db.iso(db.utcnow()), "processed": 0, "status": "idle"}},
        )
        return 0
    versions = [
        dict(row)
        for row in conn.execute(
            db.versions.select().where(db.versions.c.status == "ACTIVE")
        ).mappings()
    ]
    point_times = defaultdict(list)
    for row in pending:
        point_times[row["data"]["device_timestamp"]].append(row)
    processed = 0
    cutoff = db.utcnow() - timedelta(seconds=2)
    matches = {
        v["id"]: registry.preview(RuleConfig.model_validate(v["config"]))["matches"]
        for v in versions
    }
    for timestamp in sorted(point_times, key=db.stamp):
        batch = point_times[timestamp]
        if not force and any(db.stamp(r["data"]["received_at"]) > cutoff for r in batch):
            break
        at = db.stamp(timestamp)
        changed = {r["data"]["point_id"] for r in batch}
        candidates = []
        for version in versions:
            if version["activation"] and at < db.stamp(version["activation"]["event_time_start"]):
                continue
            for match in matches[version["id"]]:
                if not changed.intersection(match["points"].values()):
                    continue
                candidates.append((version, match))
        observations = latest_observations(
            conn,
            {point_id for _, match in candidates for point_id in match["points"].values()},
            at,
        )
        for version, match in candidates:
            evaluate_frame(conn, version, match, at, observations)
        conn.execute(
            db.outbox.update()
            .where(db.outbox.c.id.in_([row["id"] for row in batch]))
            .values(done=True)
        )
        processed += len(batch)
    db.put(
        conn,
        db.health,
        "evaluator",
        {
            "data": {
                "last_evaluated_at": db.iso(db.utcnow()),
                "processed": processed,
                "pending": pending_count - processed,
                "status": "running",
            }
        },
    )
    return processed
