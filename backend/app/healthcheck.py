import sys

from . import db


def service_is_healthy(service: str) -> bool:
    engine = db.connect()
    try:
        with engine.connect() as conn:
            row = (
                conn.execute(db.health.select().where(db.health.c.service == service))
                .mappings()
                .first()
            )
            if not row:
                return False
            timestamp = row["data"].get("heartbeat_at") or row["data"].get("last_evaluated_at")
            return bool(timestamp and (db.utcnow() - db.stamp(timestamp)).total_seconds() < 45)
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        return 2
    return 0 if service_is_healthy(args[0]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
