from fastapi import APIRouter

from ..dependencies import IssuesDep

router = APIRouter()


@router.get("/api/issues")
def list_issues(service: IssuesDep):
    return service.list_issues()


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
