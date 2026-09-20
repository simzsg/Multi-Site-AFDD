from fastapi import APIRouter

from app.schemas import Confirmation, RuleConfig

from ..dependencies import RulesDep

router = APIRouter()


@router.get("/api/rules")
def list_rules(service: RulesDep):
    return service.list_rules()


@router.post("/api/rules", status_code=201)
def create_rule(service: RulesDep, config: RuleConfig):
    return service.create_rule(config)


@router.get("/api/rules/{identity}")
def rule(service: RulesDep, identity: str):
    return service.rule(identity)


@router.post("/api/rules/{identity}/validate")
def validate(service: RulesDep, identity: str):
    return service.validate(identity)


@router.post("/api/rules/{identity}/preview")
def preview(service: RulesDep, identity: str):
    return service.preview(identity)


@router.post("/api/rules/{identity}/activate")
def activate(service: RulesDep, identity: str, confirmation: Confirmation):
    return service.activate(identity, confirmation)


@router.post("/api/rules/{identity}/disable")
def disable(service: RulesDep, identity: str):
    return service.disable(identity)


@router.post("/api/rules/{identity}/adjust", status_code=201)
def adjust(service: RulesDep, identity: str, config: RuleConfig):
    return service.adjust(identity, config)


@router.get("/api/rules/{identity}/versions")
def rule_versions(service: RulesDep, identity: str):
    return service.rule_versions(identity)


@router.get("/api/rule-schema")
def rule_schema():
    return RuleConfig.model_json_schema()
