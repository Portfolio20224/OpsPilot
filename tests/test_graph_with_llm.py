from datetime import datetime

from app.core.correlation import DeploymentCorrelator
from app.core.evidence import EvidenceBuilder
from app.core.graph import IncidentGraph
from app.core.reasoning import IncidentReasoner
from app.core.retrieval import IncidentRetriever
from app.models.schemas import (
    DiagnosisStatus,
    Incident,
    Severity,
)
from app.repositories.deployments import DeploymentRepository
from app.repositories.incidents import IncidentRepository
from app.core.recommendations import RecommendationEngine

class FakeResponse:
    content = """
    {
        "root_cause": "Database connection pool exhaustion due to N+1 query in new release",
        "confidence": 0.94,
        "reasoning": "Two confirmed historical incidents show the same symptoms and root cause."
    }
    """


class FakeModel:
    def invoke(self, prompt: str):
        return FakeResponse()
    
class LowConfidenceResponse:
    content = """
    {
        "root_cause": "Unknown",
        "confidence": 0.45,
        "reasoning": "The available evidence is insufficient to determine the root cause."
    }
    """

class LowConfidenceModel:
    def invoke(self, prompt: str):
        return LowConfidenceResponse()


def test_full_incident_graph_with_llm():
    incident_repository = IncidentRepository(
        "acmepay_dataset/incidents.json"
    )

    deployment_repository = DeploymentRepository(
        "acmepay_dataset/deployments.json"
    )

    retriever = IncidentRetriever(
        incident_repository
    )

    correlator = DeploymentCorrelator(
        deployment_repository,
        max_minutes=60,
    )

    evidence_builder = EvidenceBuilder()

    reasoner = IncidentReasoner(
        FakeModel()
    )
    recommendation_engine = RecommendationEngine()

    graph = IncidentGraph(
        retriever=retriever,
        correlator=correlator,
        evidence_builder=evidence_builder,
        reasoner=reasoner,
        recommendation_engine=recommendation_engine,
    ).build()

    current_incident = Incident(
        id="CURRENT-001",
        service="payment-api",
        severity=Severity.SEV_1,
        diagnosis_status=DiagnosisStatus.INVESTIGATING,
        timestamp=datetime.fromisoformat(
            "2026-10-06T09:17:00"
        ),
        category="connection_pool_exhaustion",
        title="Payment API elevated 5xx errors",
        symptoms=[
            "HTTP 5xx",
            "database connection timeouts",
        ],
        root_cause="Unknown",
        resolution=[],
        recent_deployment="2.14.3",
    )

    result = graph.invoke(
        {
            "incident": current_incident,
        }
    )

    assert len(result["retrieved_incidents"]) == 3
    assert result["retrieved_incidents"][0].incident.id == "INC-0500"
    assert len(result["deployment_correlations"]) == 1
    assert len(result["evidence"].incident_evidence) == 3


    assert result["diagnosis"] is not None

    assert (
        result["diagnosis"].root_cause
        == "Database connection pool exhaustion due to N+1 query in new release"
    )

    assert result["diagnosis"].confidence == 0.94

    assert (
        "confirmed historical incidents"
        in result["diagnosis"].reasoning
    )

    assert result["status"] == "recommendations_ready"

    assert len(result["recommended_actions"]) == 1

    action = result["recommended_actions"][0]

    assert action.action == "Roll back deployment 2.14.3"

    assert "INC-0500" in action.evidence_ids
    assert "INC-0510" in action.evidence_ids
    assert "DEP-001" in action.evidence_ids


def test_graph_requires_human_validation_for_low_confidence():
    incident_repository = IncidentRepository(
        "acmepay_dataset/incidents.json"
    )

    deployment_repository = DeploymentRepository(
        "acmepay_dataset/deployments.json"
    )

    retriever = IncidentRetriever(
        incident_repository
    )

    correlator = DeploymentCorrelator(
        deployment_repository,
        max_minutes=60,
    )

    evidence_builder = EvidenceBuilder()

    reasoner = IncidentReasoner(
        LowConfidenceModel()
    )
    recommendation_engine = RecommendationEngine()

    graph = IncidentGraph(
        retriever=retriever,
        correlator=correlator,
        evidence_builder=evidence_builder,
        reasoner=reasoner,
        recommendation_engine=recommendation_engine,
    ).build()

    current_incident = Incident(
        id="CURRENT-001",
        service="payment-api",
        severity=Severity.SEV_1,
        diagnosis_status=DiagnosisStatus.INVESTIGATING,
        timestamp=datetime.fromisoformat(
            "2026-10-06T09:17:00"
        ),
        category="connection_pool_exhaustion",
        title="Payment API elevated 5xx errors",
        symptoms=[
            "HTTP 5xx",
            "database connection timeouts",
        ],
        root_cause="Unknown",
        resolution=[],
        recent_deployment="2.14.3",
    )

    result = graph.invoke(
        {
            "incident": current_incident,
        }
    )

    assert result["diagnosis"] is not None

    assert (
        result["diagnosis"].root_cause
        == "Unknown"
    )

    assert result["diagnosis"].confidence == 0.45

    assert (
        "evidence is insufficient"
        in result["diagnosis"].reasoning
    )

    assert result["status"] == "human_validation_required"