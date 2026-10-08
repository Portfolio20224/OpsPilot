from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import get_incident_graph

from app.core.exceptions import (
    LLMResponseError,
    LLMTimeoutError,
)

class TimeoutGraph:
    def invoke(self, state):
        raise LLMTimeoutError("LLM request timed out")
    
class FailingLLMGraph:
    def invoke(self, state):
        raise LLMResponseError("LLM diagnosis failed")

class FakeGraph:
    def invoke(self, state):
        incident = state["incident"]

        return {
            "incident": incident,
            "status": "recommendations_ready",
            "diagnosis": {
                "root_cause": "Database connection pool exhaustion",
                "confidence": 0.95,
                "reasoning": (
                    "A recent deployment occurred shortly before "
                    "the incident and historical incidents show "
                    "the same failure pattern."
                ),
            },
            "recommended_actions": [
                {
                    "action": "Roll back deployment 2.14.3",
                    "rationale": (
                        "The deployment occurred shortly before "
                        "the incident."
                    ),
                    "priority": 1,
                    "evidence_ids": [
                        "INC-0500",
                        "INC-0510",
                        "DEP-001",
                    ],
                }
            ],
            "evidence": None,
        }


def test_analyze_incident():
    app.dependency_overrides[get_incident_graph] = lambda: FakeGraph()

    client = TestClient(app)

    response = client.post(
        "/incidents/analyze",
        json={
            "id": "CURRENT-001",
            "service": "payment-api",
            "severity": "SEV-1",
            "timestamp": "2026-10-06T09:17:00",
            "category": "connection_pool_exhaustion",
            "title": "Payment API elevated 5xx errors",
            "symptoms": [
                "HTTP 5xx",
                "database connection timeouts",
            ],
            "recent_deployment": "2.14.3",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["request_id"]
    assert isinstance(body["request_id"], str)

    assert body["incident_id"] == "CURRENT-001"
    assert body["status"] == "recommendations_ready"

    assert body["diagnosis"]["root_cause"] == (
        "Database connection pool exhaustion"
    )
    assert body["diagnosis"]["confidence"] == 0.95

    assert len(body["recommended_actions"]) == 1
    assert body["recommended_actions"][0]["priority"] == 1

    assert "incident" not in body
    assert "retrieved_incidents" not in body
    assert "deployment_correlations" not in body
    app.dependency_overrides.clear()

def test_analyze_incident_returns_504_on_llm_timeout():
    app.dependency_overrides[get_incident_graph] = (
        lambda: TimeoutGraph()
    )

    client = TestClient(app)

    response = client.post(
        "/incidents/analyze",
        json={
            "id": "CURRENT-001",
            "service": "payment-api",
            "severity": "SEV-1",
            "timestamp": "2026-10-06T09:17:00",
            "category": "connection_pool_exhaustion",
            "title": "Payment API elevated 5xx errors",
            "symptoms": [
                "HTTP 5xx",
                "database connection timeouts",
            ],
            "recent_deployment": "2.14.3",
        },
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "LLM request timed out"

    app.dependency_overrides.clear()

def test_analyze_incident_returns_502_on_llm_error():
    app.dependency_overrides[get_incident_graph] = (
        lambda: FailingLLMGraph()
    )

    client = TestClient(app)

    response = client.post(
        "/incidents/analyze",
        json={
            "id": "CURRENT-001",
            "service": "payment-api",
            "severity": "SEV-1",
            "timestamp": "2026-10-06T09:17:00",
            "category": "connection_pool_exhaustion",
            "title": "Payment API elevated 5xx errors",
            "symptoms": [
                "HTTP 5xx",
                "database connection timeouts",
            ],
            "recent_deployment": "2.14.3",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM diagnosis failed"

    app.dependency_overrides.clear()

def test_analyze_incident_generates_unique_request_ids():
    app.dependency_overrides[get_incident_graph] = (
        lambda: FakeGraph()
    )

    client = TestClient(app)

    payload = {
        "id": "CURRENT-001",
        "service": "payment-api",
        "severity": "SEV-1",
        "timestamp": "2026-10-06T09:17:00",
        "category": "connection_pool_exhaustion",
        "title": "Payment API elevated 5xx errors",
        "symptoms": [
            "HTTP 5xx",
            "database connection timeouts",
        ],
        "recent_deployment": "2.14.3",
    }

    response_1 = client.post(
        "/incidents/analyze",
        json=payload,
    )

    response_2 = client.post(
        "/incidents/analyze",
        json=payload,
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    request_id_1 = response_1.json()["request_id"]
    request_id_2 = response_2.json()["request_id"]

    assert request_id_1 != request_id_2

    app.dependency_overrides.clear()