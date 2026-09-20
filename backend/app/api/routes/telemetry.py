from datetime import datetime

from fastapi import APIRouter, Query

from ..dependencies import TelemetryDep

router = APIRouter()


@router.get("/api/current")
def current(service: TelemetryDep):
    return service.current()


@router.get("/api/points/{identity}/latest")
def latest(service: TelemetryDep, identity: str):
    return service.latest(identity)


@router.get("/api/points/{identity}/history")
def history(
    service: TelemetryDep,
    identity: str,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(500, ge=1, le=5000),
):
    return service.history(identity, start, end, limit)
