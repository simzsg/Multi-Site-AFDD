from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.engine import Engine

from app.application.rule_service import RuleService
from app.config import Settings
from app.persistence.authoring import AuthoringQueries
from app.persistence.inventory import InventoryQueries
from app.persistence.issues import IssueQueries
from app.persistence.operations import OperationsQueries
from app.persistence.telemetry import TelemetryQueries


def get_engine(request: Request) -> Engine:
    return request.app.state.engine


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


EngineDep = Annotated[Engine, Depends(get_engine)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_inventory(engine: EngineDep) -> InventoryQueries:
    return InventoryQueries(engine)


def get_telemetry(engine: EngineDep) -> TelemetryQueries:
    return TelemetryQueries(engine)


def get_operations(engine: EngineDep, settings: SettingsDep) -> OperationsQueries:
    return OperationsQueries(engine, settings)


def get_issues(engine: EngineDep) -> IssueQueries:
    return IssueQueries(engine)


def get_authoring(engine: EngineDep) -> AuthoringQueries:
    return AuthoringQueries(engine)


def get_rules(engine: EngineDep, settings: SettingsDep) -> RuleService:
    return RuleService(engine, settings.source_replay_start)


InventoryDep = Annotated[InventoryQueries, Depends(get_inventory)]
TelemetryDep = Annotated[TelemetryQueries, Depends(get_telemetry)]
OperationsDep = Annotated[OperationsQueries, Depends(get_operations)]
IssuesDep = Annotated[IssueQueries, Depends(get_issues)]
AuthoringDep = Annotated[AuthoringQueries, Depends(get_authoring)]
RulesDep = Annotated[RuleService, Depends(get_rules)]
