from collections import defaultdict
from datetime import timedelta
from uuid import uuid4

from . import db
from .ontology import Registry
from .schemas import RuleConfig


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
    registry = Registry(conn)
    pending = [
        dict(r)
        for r in conn.execute(db.outbox.select().where(db.outbox.c.done.is_(False))).mappings()
    ]
    if not pending:
        db.put(
            conn,
            db.health,
            "evaluator",
            {"data": {"last_evaluated_at": db.iso(db.utcnow()), "processed": 0, "status": "idle"}},
        )
        return 0
    versions = [v for v in db.rows(conn, db.versions) if v["status"] == "ACTIVE"]
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
        for version in versions:
            if version["activation"] and at < db.stamp(version["activation"]["event_time_start"]):
                continue
            for match in matches[version["id"]]:
                if not changed.intersection(match["points"].values()):
                    continue
                observations = {}
                for point_id in match["points"].values():
                    r = (
                        conn.execute(
                            db.telemetry.select()
                            .where(
                                db.telemetry.c.point_id == point_id,
                                db.telemetry.c.device_timestamp <= at,
                            )
                            .order_by(db.telemetry.c.device_timestamp.desc())
                            .limit(1)
                        )
                        .mappings()
                        .first()
                    )
                    if r:
                        observations[point_id] = {
                            **dict(r),
                            "device_timestamp": db.iso(r["device_timestamp"]),
                            "received_at": db.iso(r["received_at"]),
                        }
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
                "pending": len(pending) - processed,
                "status": "running",
            }
        },
    )
    return processed
