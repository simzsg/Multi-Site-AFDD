import hashlib
import json
from datetime import timedelta

from pydantic import ValidationError
from sqlalchemy import and_

from . import db
from .schemas import Observation


def ingest(conn, payload):
    now = db.utcnow()
    try:
        if isinstance(payload, dict) and payload.get("source_error"):
            raise ValueError(payload["source_error"])
        observation = Observation.model_validate(payload)
        point = (
            conn.execute(db.entities.select().where(db.entities.c.id == observation.point_id))
            .mappings()
            .first()
        )
        if not point or "unit" not in point["data"]:
            raise ValueError("Unknown point identity")
        if point["data"]["unit"] != observation.unit:
            raise ValueError("Wrong unit")
        if point["data"].get("value_kind") == "binary" and observation.value not in (0, 1, None):
            raise ValueError("Binary point must be 0 or 1")
        if observation.device_timestamp > now + timedelta(minutes=5):
            raise ValueError("Device timestamp more than five minutes in future")
        data = observation.model_dump(mode="json")
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        db.lock(conn, "event_receipt", observation.event_id)
        receipt = (
            conn.execute(db.receipts.select().where(db.receipts.c.event_id == observation.event_id))
            .mappings()
            .first()
        )
        if receipt:
            if receipt["digest"] != digest:
                raise ValueError("Event ID reused with different content")
            db.log(conn, "duplicate", event_id=observation.event_id, point_id=observation.point_id)
            return {"status": "duplicate"}
        collision = conn.execute(
            db.telemetry.select().where(
                and_(
                    db.telemetry.c.point_id == observation.point_id,
                    db.telemetry.c.device_timestamp == observation.device_timestamp,
                )
            )
        ).first()
        if collision:
            raise ValueError("Conflicting observation at existing point timestamp")
        conn.execute(
            db.receipts.insert().values(
                event_id=observation.event_id, digest=digest, received_at=now
            )
        )
        conn.execute(db.telemetry.insert().values(**observation.model_dump(), received_at=now))
        latest = (
            conn.execute(db.current.select().where(db.current.c.point_id == observation.point_id))
            .mappings()
            .first()
        )
        is_newer = (
            not latest
            or db.stamp(latest["data"]["device_timestamp"]) < observation.device_timestamp
        )
        if latest and is_newer:
            gap_seconds = (
                observation.device_timestamp - db.stamp(latest["data"]["device_timestamp"])
            ).total_seconds()
            expected = point["data"].get("expected_interval_seconds", 60)
            previous_source = latest["data"].get("source") or {}
            entering_live_timeline = (
                observation.source.get("mode") == "live-source"
                and previous_source.get("mode") != "live-source"
            )
            if not entering_live_timeline and gap_seconds > expected * 1.5:
                db.log(
                    conn,
                    "data_gap",
                    point_id=observation.point_id,
                    event_id=observation.event_id,
                    previous_at=latest["data"]["device_timestamp"],
                    next_at=data["device_timestamp"],
                    gap_seconds=gap_seconds,
                )
        if not is_newer:
            db.log(
                conn,
                "late",
                point_id=observation.point_id,
                event_id=observation.event_id,
                device_timestamp=data["device_timestamp"],
            )
        if observation.quality == "MISSING":
            db.log(
                conn,
                "incomplete",
                point_id=observation.point_id,
                event_id=observation.event_id,
                source=observation.source,
            )
        if is_newer:
            db.put(
                conn,
                db.current,
                observation.point_id,
                {"data": {**data, "received_at": db.iso(now)}},
            )
        conn.execute(
            db.outbox.insert().values(data={**data, "received_at": db.iso(now)}, done=False)
        )
        db.put(
            conn,
            db.health,
            "ingestion",
            {
                "data": {
                    "last_received_at": db.iso(now),
                    "last_device_timestamp": data["device_timestamp"],
                    "lag_seconds": max(0, (now - observation.device_timestamp).total_seconds()),
                    "status": "running",
                }
            },
        )
        return {"status": "accepted", "current_updated": is_newer}
    except (ValueError, ValidationError) as exc:
        reason = str(exc)
        db.log(
            conn,
            "rejected",
            event_id=payload.get("event_id") if isinstance(payload, dict) else None,
            reason=reason,
            payload=payload,
        )
        return {"status": "rejected", "reason": reason}
