import httpx
from app import ai, db
from app.main import create_app
from app.schemas import AIRequest, RuleConfig
from fastapi.testclient import TestClient


def test_api_human_gate(engine):
    with TestClient(create_app(engine)) as client:
        assert client.get("/api/health").status_code == 200
        result = client.post(
            "/api/ai/requests", json={"prompt": ai.DEMO_PROMPT, "mode": "demo"}
        ).json()
        assert result["state"] == "DRAFT_READY"
        v = result["draft"]
        assert v["status"] == "DRAFT"
        assert (
            client.post(
                f"/api/rules/{v['id']}/activate",
                json={
                    "confirmed": False,
                    "preview_digest": result["preview"]["digest"],
                    "reviewer": "test",
                },
            ).status_code
            == 422
        )
        assert (
            client.post(
                f"/api/rules/{v['id']}/activate",
                json={
                    "confirmed": True,
                    "preview_digest": result["preview"]["digest"],
                    "reviewer": "test",
                },
            ).status_code
            == 200
        )
        assert client.get(f"/api/ai/requests/{result['id']}").json()["data"]["state"] == "ACTIVATED"
        assert client.get("/api/issues").json() == []
        assert len(client.get("/api/buildings").json()) == 3
        assert client.get("/api/points/absent/latest").status_code == 404
        assert client.get("/openapi.json").status_code == 200


def test_ai_no_match_invented_and_missing(engine):
    for config, expected in [
        (RuleConfig(target={"space_use": "nonexistent"}), "NO_MATCH"),
        (RuleConfig(target={"building_ids": ["invented"]}), "INVALID_TOOL_OUTPUT"),
    ]:
        result = ai.author(
            engine,
            AIRequest(prompt="A supported natural language request", mode="model"),
            provider=lambda *args, config=config: {
                "state": "DRAFT",
                "message": "test stub",
                "config_json": config.model_dump_json(),
            },
        )
        assert result["state"] == expected
    result = ai.author(
        engine, AIRequest(prompt="Compare room IAQ with return air above five degrees", mode="demo")
    )
    assert result["state"] == "NEEDS_CLARIFICATION"
    with engine.connect() as conn:
        assert not db.rows(conn, db.versions)


def test_ai_retry_timeout_and_invalid_output(engine):
    attempts = []

    def transient(*args):
        attempts.append(1)
        if len(attempts) == 1:
            raise httpx.ConnectError("temporary")
        return {"state": "DRAFT", "message": "test", "config_json": RuleConfig().model_dump_json()}

    assert (
        ai.author(engine, AIRequest(prompt="Valid request with details"), provider=transient)[
            "state"
        ]
        == "DRAFT_READY"
    )
    assert len(attempts) == 2

    def timeout(*args):
        raise httpx.ReadTimeout("timeout")

    assert (
        ai.author(engine, AIRequest(prompt="Valid request with details"), provider=timeout)["state"]
        == "TIMEOUT"
    )
    assert (
        ai.author(
            engine,
            AIRequest(prompt="Valid request with details"),
            provider=lambda *args: {"state": "ACTIVATE_NOW"},
        )["state"]
        == "INVALID_TOOL_OUTPUT"
    )
