from datetime import timedelta

import pytest
from app import db
from app.ingestion import ingest
from app.main import create_app
from app.schemas import RuleConfig
from fastapi.testclient import TestClient
from test_core import BASE, EQ, event


@pytest.fixture
def client(engine):
    with TestClient(create_app(engine)) as client:
        yield client


def test_discovery_and_served_relationship_contract(client):
    entities = client.get("/api/entities").json()
    assert all(entity["semantic_type"].startswith(("https://", "urn:")) for entity in entities)
    for path, kind in [
        ("buildings", "Building"),
        ("floors", "Floor"),
        ("zones", "HVAC_Zone"),
        ("rooms", "Room"),
    ]:
        expected = [entity for entity in entities if entity["kind"] == kind]
        assert client.get(f"/api/{path}").json() == expected
        assert client.get("/api/entities", params={"kind": kind}).json() == expected
    assert client.get("/api/buildings?kind=Floor").json() == client.get("/api/floors").json()
    assert {item["kind"] for item in client.get("/api/equipment").json()} == {
        "AHU",
        "IAQ_Device",
        "Electrical_Meter",
    }
    assert all("unit" in point["data"] for point in client.get("/api/points").json())
    edges = client.get("/api/relationships").json()
    assert all(edge["semantic_relation"].startswith("https://") for edge in edges)
    assert client.get(f"/api/equipment/{EQ}/relationships").json() == [
        edge for edge in edges if EQ in (edge["source"], edge["target"])
    ]
    served = client.get(f"/api/equipment/{EQ}/served-spaces").json()
    assert served["label"] == "Potentially affected"
    assert len(served["zones"]) == 1
    assert len(served["rooms"]) == 2
    assert {room["id"] for room in served["rooms"]}.isdisjoint(
        item["id"] for item in served["installation"]
    )
    zone = served["zones"][0]["id"]
    assert client.get(f"/api/zones/{zone}/rooms").json() == served["rooms"]
    ontology = client.get("/api/ontology").json()
    assert ontology["brick_version"] == "1.4.4"
    assert ontology["entity_types"]["AHU"].endswith("#AHU")
    assert ontology["relationships"]["measuresSpace"].endswith("#meters")
    for path in ["relationships", "served-spaces"]:
        response = client.get(f"/api/equipment/absent/{path}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}
    assert client.get("/api/zones/absent/rooms").status_code == 404


def test_telemetry_missing_history_order_bounds_and_limit(client, engine):
    kind = "Supply_Air_Temperature_Sensor"
    point = f"{EQ}-{kind}"
    assert client.get(f"/api/points/{point}/latest").json() == {"status": "MISSING"}
    assert client.get(f"/api/points/{point}/history").json() == []
    for endpoint in ["latest", "history"]:
        response = client.get(f"/api/points/absent/{endpoint}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}
    with db.transaction(engine) as conn:
        for minute in [3, 0, 2, 1]:
            payload = event(kind, minute, None if minute == 2 else 18 + minute)
            if minute == 2:
                payload["quality"] = "MISSING"
            payload["source"] = {"file": "contract-fixture.csv"}
            assert ingest(conn, payload)["status"] == "accepted"
    history = client.get(f"/api/points/{point}/history").json()
    assert [row["value"] for row in history] == [18, 19, None, 21]
    assert history[2]["quality"] == "MISSING"
    assert history[2]["source"] == {"file": "contract-fixture.csv"}
    assert all("received_at" in row for row in history)
    assert client.get(f"/api/points/{point}/history?limit=2").json() == history[2:]
    bounded = client.get(
        f"/api/points/{point}/history",
        params={
            "start": db.iso(BASE + timedelta(minutes=1)),
            "end": db.iso(BASE + timedelta(minutes=2)),
        },
    )
    assert bounded.json() == history[1:3]
    latest = client.get(f"/api/points/{point}/latest").json()
    assert latest["value"] == 21
    assert client.get("/api/current").json()[point] == latest
    for invalid in [{"limit": 0}, {"limit": 5001}, {"start": "not-a-date"}]:
        assert client.get(f"/api/points/{point}/history", params=invalid).status_code == 422


def test_rule_versions_confirmation_disable_and_audit_contract(client):
    config = RuleConfig().model_dump()
    response = client.post("/api/rules", json=config)
    assert response.status_code == 201
    first = response.json()
    assert first["version"] == 1
    assert first["status"] == "DRAFT"
    identity = first["id"]
    assert client.post(f"/api/rules/{identity}/validate").json() == {"valid": True, "errors": []}
    preview = client.post(f"/api/rules/{identity}/preview").json()
    assert len(preview["matches"]) == 24
    confirmation = {"confirmed": True, "reviewer": "HTTP contract test", "preview_digest": "stale"}
    response = client.post(f"/api/rules/{identity}/activate", json=confirmation)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Preview changed; review the current targets before confirming"
    }
    assert client.get(f"/api/rules/{identity}").json() == first
    confirmation["preview_digest"] = preview["digest"]
    activated = client.post(f"/api/rules/{identity}/activate", json=confirmation).json()
    assert activated["status"] == "ACTIVE"
    assert activated["activation"]["reviewer"] == confirmation["reviewer"]
    adjusted = {**config, "name": "Reviewed revision", "logic": {**config["logic"], "threshold": 4}}
    response = client.post(f"/api/rules/{identity}/adjust", json=adjusted)
    assert response.status_code == 201
    second = response.json()
    assert second["version"] == 2
    assert second["rule_id"] == first["rule_id"]
    assert second["status"] == "DRAFT"
    assert client.get(f"/api/rules/{identity}").json() == activated
    assert client.get(f"/api/rules/{second['id']}/versions").json() == [activated, second]
    assert client.post(f"/api/rules/{identity}/disable").json() == {"status": "DISABLED"}
    assert client.get(f"/api/rules/{identity}").json()["status"] == "DISABLED"
    assert client.get(f"/api/rules/{second['id']}").json() == second
    audit = client.get("/api/audit", params={"action": "rule_drafted", "limit": 1}).json()
    assert len(audit) == 1
    assert audit[0]["action"] == "rule_drafted"
    assert audit[0]["data"]["rule_version"] == second["id"]
    assert client.get("/api/audit?action=absent").json() == []
    assert client.get("/api/audit?limit=1001").status_code == 422
    for operation in ["validate", "preview", "disable"]:
        assert client.post(f"/api/rules/absent/{operation}").status_code == 404
    assert client.get("/api/rules/absent/versions").status_code == 404


def test_issue_list_filters_and_bounds(client, engine):
    with db.transaction(engine) as conn:
        conn.execute(
            db.issues.insert(),
            [
                {
                    "id": "issue-old",
                    "version_id": "version",
                    "equipment_id": EQ,
                    "status": "RECOVERED",
                    "data": {"created_at": "2026-01-01T00:00:00+00:00"},
                },
                {
                    "id": "issue-new",
                    "version_id": "version",
                    "equipment_id": "other-equipment",
                    "status": "ACTIVE",
                    "data": {"created_at": "2026-01-02T00:00:00+00:00"},
                },
            ],
        )
    assert [row["id"] for row in client.get("/api/issues").json()] == [
        "issue-new",
        "issue-old",
    ]
    assert [row["id"] for row in client.get("/api/issues", params={"status": "ACTIVE"}).json()] == [
        "issue-new"
    ]
    assert [row["id"] for row in client.get("/api/issues", params={"equipment_id": EQ}).json()] == [
        "issue-old"
    ]
    assert [
        row["id"] for row in client.get("/api/issues", params={"limit": 1, "offset": 1}).json()
    ] == ["issue-old"]
    assert client.get("/api/issues", params={"limit": 0}).status_code == 422
    assert client.get("/api/issues", params={"offset": -1}).status_code == 422
