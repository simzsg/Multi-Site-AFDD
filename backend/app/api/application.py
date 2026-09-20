from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine

from app import db, schema
from app.config import Settings
from app.persistence.records import RecordNotFound

from .routes import authoring, inventory, issues, operations, rules, telemetry


def create_app(engine: Engine | None = None, *, settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.engine = (
            engine if engine is not None else db.connect(settings.database_url)
        )
        try:
            schema.require_current(application.state.engine)
            yield
        finally:
            if engine is None:
                application.state.engine.dispose()

    application = FastAPI(title="Alto / Multi-Site AFDD", version="0.1.0", lifespan=lifespan)
    application.state.settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(ValueError)
    async def bad_request(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @application.exception_handler(RecordNotFound)
    async def not_found(request: Request, exc: RecordNotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    for module in (operations, inventory, telemetry, rules, issues, authoring):
        application.include_router(module.router)
    return application
