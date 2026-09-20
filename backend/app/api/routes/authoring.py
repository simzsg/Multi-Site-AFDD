from fastapi import APIRouter

from app import ai
from app.schemas import AIRequest

from ..dependencies import AuthoringDep, EngineDep

router = APIRouter()


@router.get("/api/ai/requests")
def ai_history(service: AuthoringDep):
    return service.ai_history()


@router.get("/api/ai/requests/{identity}")
def ai_request(service: AuthoringDep, identity: str):
    return service.ai_request(identity)


@router.post("/api/ai/requests", status_code=201)
def ai_author(engine: EngineDep, request: AIRequest):
    return ai.author(engine, request)
