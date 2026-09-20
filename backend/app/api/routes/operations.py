from fastapi import APIRouter, Query

from ..dependencies import OperationsDep

router = APIRouter()


@router.get("/api/health")
def health(service: OperationsDep):
    return service.health()


@router.get("/api/pipeline-health")
def pipeline(service: OperationsDep):
    return service.pipeline()


@router.get("/api/ingestion-health")
def ingestion_health(service: OperationsDep):
    return service.ingestion_health()


@router.get("/api/evaluator-health")
def evaluator_health(service: OperationsDep):
    return service.evaluator_health()


@router.get("/api/audit")
def audit(
    service: OperationsDep, limit: int = Query(100, ge=1, le=1000), action: str | None = None
):
    return service.audit(limit, action)
