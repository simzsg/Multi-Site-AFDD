import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from app import cli, db, schema
from app.api.application import create_app
from app.application.rule_service import RuleService
from app.config import Settings
from app.schemas import Confirmation, RuleConfig
from fastapi.testclient import TestClient
from sqlalchemy import func, select


def test_ontology_domain_has_no_database_dependency():
    source = Path("backend/app/ontology.py").read_text()
    tree = ast.parse(source)
    modules = {
        name.name for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names
    } | {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imported_names = {
        name.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for name in node.names
    }
    assert "db" not in imported_names
    assert not any(module.startswith("sqlalchemy") for module in modules)


@pytest.mark.parametrize("migration_fails", [False, True])
def test_owned_engine_is_deferred_and_disposed_even_on_startup_failure(
    monkeypatch, migration_fails
):
    owned_engine = Mock()
    connect = Mock(return_value=owned_engine)
    check_schema = Mock(side_effect=RuntimeError("migration failed") if migration_fails else None)
    monkeypatch.setattr(db, "connect", connect)
    monkeypatch.setattr(schema, "require_current", check_schema)
    settings = Settings(database_url="sqlite:///owned-by-application.db")
    application = create_app(settings=settings)
    connect.assert_not_called()
    check_schema.assert_not_called()
    if migration_fails:
        with pytest.raises(RuntimeError, match="migration failed"), TestClient(application):
            pytest.fail("Startup must fail before serving requests")
    else:
        with TestClient(application):
            assert application.state.engine is owned_engine
            owned_engine.dispose.assert_not_called()
    connect.assert_called_once_with(settings.database_url)
    check_schema.assert_called_once_with(owned_engine)
    owned_engine.dispose.assert_called_once_with()


@pytest.mark.parametrize("migration_fails", [False, True])
def test_injected_engine_remains_caller_owned(monkeypatch, migration_fails):
    injected_engine = Mock()
    connect = Mock(side_effect=AssertionError("Must use the caller's engine"))
    check_schema = Mock(side_effect=RuntimeError("migration failed") if migration_fails else None)
    monkeypatch.setattr(db, "connect", connect)
    monkeypatch.setattr(schema, "require_current", check_schema)
    application = create_app(injected_engine, settings=Settings())
    if migration_fails:
        with pytest.raises(RuntimeError, match="migration failed"), TestClient(application):
            pytest.fail("Startup must fail before serving requests")
    else:
        with TestClient(application):
            assert application.state.engine is injected_engine
    connect.assert_not_called()
    check_schema.assert_called_once_with(injected_engine)
    injected_engine.dispose.assert_not_called()


def test_activation_rolls_back_rule_audit_and_linked_ai_updates(engine, monkeypatch):
    service = RuleService(engine)
    draft = service.create_rule(RuleConfig())
    before_requests = [
        {"id": identity, "data": {"state": "DRAFT_READY", "draft": draft}}
        for identity in ["authoring-first", "authoring-second"]
    ]
    with db.transaction(engine) as conn:
        for request in before_requests:
            db.put(conn, db.ai_requests, request["id"], {"data": request["data"]})
        before_audit = db.rows(conn, db.audit)
    original_put = db.put
    attempted = []

    def fail_after_linked_update(conn, table, key, value):
        original_put(conn, table, key, value)
        if table is db.ai_requests:
            attempted.append(key)
            if len(attempted) == 2:
                raise RuntimeError("Linked authoring persistence failed")

    monkeypatch.setattr(db, "put", fail_after_linked_update)
    confirmation = Confirmation(
        confirmed=True,
        reviewer="Application boundary test",
        preview_digest=service.preview(draft["id"])["digest"],
    )
    with pytest.raises(RuntimeError, match="Linked authoring persistence failed"):
        service.activate(draft["id"], confirmation)
    assert len(attempted) == 2
    assert service.rule(draft["id"]) == draft
    with engine.connect() as conn:
        assert db.rows(conn, db.ai_requests) == before_requests
        assert db.rows(conn, db.audit) == before_audit


def test_explicit_live_clock_does_not_inherit_replay_environment(engine, monkeypatch):
    monkeypatch.setenv("SOURCE_REPLAY_START", "2026-01-15T08:00:00Z")
    service = RuleService(engine, Settings().source_replay_start)
    draft = service.create_rule(RuleConfig())
    preview = service.preview(draft["id"])
    active = service.activate(
        draft["id"],
        Confirmation(
            confirmed=True,
            preview_digest=preview["digest"],
            reviewer="Explicit live settings",
        ),
    )
    assert active["activation"]["clock_mode"] == "LIVE"
    assert not active["activation"]["event_time_start"].startswith("2026-01-15")


def test_importing_workflows_does_not_read_environment_files():
    code = """
import dotenv
from unittest.mock import Mock
dotenv.load_dotenv = Mock(side_effect=AssertionError("import read .env"))
import app.runtime
import app.workers.ingestion
import app.application.rule_service
import app.healthcheck
dotenv.load_dotenv.assert_not_called()
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "PYTHONPATH": "backend"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_cli_migrate_seed_uses_selected_database(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'commands.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cli.main(["migrate"])
    cli.main(["seed", "--synthetic"])
    engine = db.connect(url)
    try:
        with engine.begin() as conn:
            conn.execute(
                db.entities.insert().values(id="temporary", kind="Room", label="Temporary", data={})
            )
        cli.main(["reset", "--confirm-reset"])
        with engine.connect() as conn:
            assert conn.execute(select(func.count()).select_from(db.entities)).scalar() == 465
            assert (
                conn.execute(
                    select(func.count())
                    .select_from(db.entities)
                    .where(db.entities.c.id == "temporary")
                ).scalar()
                == 0
            )
    finally:
        engine.dispose()


def test_jsonl_replay_preserves_envelopes_stream_and_closes_client(tmp_path, monkeypatch):
    source = tmp_path / "observations.jsonl"
    payload = {"event_id": "source-id", "device_timestamp": "2026-01-15T08:00:00Z", "value": None}
    source.write_text(json.dumps(payload) + "\n")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'unused.db'}")
    monkeypatch.setenv("TELEMETRY_STREAM", "chosen-stream")

    class Broker:
        closed = False
        messages = []

        def xadd(self, stream, data):
            self.messages.append((stream, json.loads(data["payload"])))

        def close(self):
            self.closed = True

    broker = Broker()
    monkeypatch.setattr(cli.Redis, "from_url", lambda url, decode_responses: broker)
    cli.main(["replay", "--file", str(source)])
    assert broker.messages == [("chosen-stream", payload)]
    assert broker.closed
    broker.closed = False
    source.write_text("{bad json")
    with pytest.raises(json.JSONDecodeError):
        cli.main(["replay", "--file", str(source)])
    assert broker.closed


def test_cli_rejects_incomplete_replay_before_constructing_dependencies(monkeypatch):
    def unexpected_connect(*args):
        pytest.fail("Invalid CLI arguments must fail before allocating a database engine")

    monkeypatch.setattr(cli.db, "connect", unexpected_connect)
    with pytest.raises(SystemExit) as result:
        cli.main(["replay"])
    assert result.value.code == 2
    with pytest.raises(SystemExit) as result:
        cli.main(["reset"])
    assert result.value.code == 2
