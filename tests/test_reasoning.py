from datetime import timedelta

from app.models.schemas import (
    DeploymentEvidence,
    EvidencePackage,
    IncidentEvidence,
)
from app.core.reasoning import IncidentReasoner
import pytest

from app.core.exceptions import (
    LLMResponseError,
    LLMTimeoutError,
)


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeModel:
    def invoke(self, prompt):
        return FakeResponse(
            '{"root_cause": "Database connection pool exhaustion", '
            '"confidence": 0.9, '
            '"reasoning": "Historical incidents match the symptoms."}'
        )


class TimeoutModel:
    def invoke(self, prompt):
        raise TimeoutError("request timed out")


class InvalidResponseModel:
    def invoke(self, prompt):
        return FakeResponse(
            "This is not valid JSON"
        )
@pytest.fixture
def evidence_package():    
    return EvidencePackage(
        incident_evidence=[
            IncidentEvidence(
                incident_id="INC-0500",
                similarity_score=0.943,
                diagnosis_status="confirmed",
                service="payment-api",
                category="connection_pool_exhaustion",
                symptoms=[
                    "HTTP 5xx",
                    "database connection timeouts",
                ],
                root_cause=(
                    "Database connection pool exhaustion "
                    "due to N+1 query in new release"
                ),
                resolution=[
                    "Rolled back deployment 2.8.9"
                ],
                recent_deployment="2.8.9",
            ),
            IncidentEvidence(
                incident_id="INC-0505",
                similarity_score=0.943,
                diagnosis_status="unknown",
                service="payment-api",
                category="connection_pool_exhaustion",
                symptoms=[
                    "HTTP 5xx",
                    "database connection timeouts",
                ],
                root_cause="Unknown",
                resolution=[
                    "Restarted pods. Works now."
                ],
                recent_deployment="2.11.9",
            ),
        ],
        deployment_evidence=[
            DeploymentEvidence(
                deployment_id="DEP-001",
                service="payment-api",
                version="2.14.3",
                previous_version="2.14.2",
                deployed_at="2026-10-06T09:03:00",
                incident_time_delta=timedelta(minutes=14),
                status="success",
            )
        ],
    )
    
def test_reasoner_returns_diagnosis(evidence_package):
    reasoner = IncidentReasoner(FakeModel())

    diagnosis = reasoner.diagnose(evidence_package)

    assert diagnosis.root_cause == (
        "Database connection pool exhaustion"
    )
    assert diagnosis.confidence == 0.9


def test_reasoner_handles_timeout(evidence_package):
    reasoner = IncidentReasoner(TimeoutModel())

    with pytest.raises(LLMTimeoutError):
        reasoner.diagnose(evidence_package)


def test_reasoner_handles_invalid_response(evidence_package):
    reasoner = IncidentReasoner(InvalidResponseModel())

    with pytest.raises(LLMResponseError):
        reasoner.diagnose(evidence_package)

class FakeModels:
    def invoke(self, prompt: str):
        class FakeResponse:
            content = """
            {
                "root_cause": "Database connection pool exhaustion due to N+1 query in new release",
                "confidence": 0.94,
                "reasoning": "Two confirmed historical incidents show the same symptoms and root cause."
            }
            """

        return FakeResponse()


def test_incident_reasoner():
    evidence = EvidencePackage(
        incident_evidence=[
            IncidentEvidence(
                incident_id="INC-0500",
                similarity_score=0.943,
                diagnosis_status="confirmed",
                service="payment-api",
                category="connection_pool_exhaustion",
                symptoms=[
                    "HTTP 5xx",
                    "database connection timeouts",
                ],
                root_cause=(
                    "Database connection pool exhaustion "
                    "due to N+1 query in new release"
                ),
                resolution=[
                    "Rolled back deployment 2.8.9"
                ],
                recent_deployment="2.8.9",
            ),
            IncidentEvidence(
                incident_id="INC-0505",
                similarity_score=0.943,
                diagnosis_status="unknown",
                service="payment-api",
                category="connection_pool_exhaustion",
                symptoms=[
                    "HTTP 5xx",
                    "database connection timeouts",
                ],
                root_cause="Unknown",
                resolution=[
                    "Restarted pods. Works now."
                ],
                recent_deployment="2.11.9",
            ),
        ],
        deployment_evidence=[
            DeploymentEvidence(
                deployment_id="DEP-001",
                service="payment-api",
                version="2.14.3",
                previous_version="2.14.2",
                deployed_at="2026-10-06T09:03:00",
                incident_time_delta=timedelta(minutes=14),
                status="success",
            )
        ],
    )

    reasoner = IncidentReasoner(FakeModels())

    diagnosis = reasoner.diagnose(evidence)

    assert diagnosis.root_cause == (
        "Database connection pool exhaustion "
        "due to N+1 query in new release"
    )

    assert diagnosis.confidence == 0.94

    assert "confirmed historical incidents" in diagnosis.reasoning