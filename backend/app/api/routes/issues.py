from fastapi import APIRouter, Query

from ..dependencies import IssuesDep

router = APIRouter()


@router.get("/api/issues")
def list_issues(
    service: IssuesDep,
    status: str | None = None,
    equipment_id: str | None = None,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    return service.list_issues(status, equipment_id, limit, offset)


@router.get("/api/issues/{identity}")
def issue(service: IssuesDep, identity: str):
    return service.issue(identity)


@router.get("/api/issues/{identity}/evidence")
def evidence(service: IssuesDep, identity: str):
    return service.evidence(identity)


@router.get("/api/issues/{identity}/affected-spaces")
def affected(service: IssuesDep, identity: str):
    return service.affected(identity)


@router.get("/api/evaluation-states")
def evaluation_states(service: IssuesDep):
    return service.evaluation_states()
