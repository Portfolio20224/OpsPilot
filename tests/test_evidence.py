from app.core.correlation import DeploymentCorrelator
from app.core.evidence import EvidenceBuilder
from app.core.retrieval import IncidentRetriever
from app.models.schemas import Incident
from app.repositories.deployments import DeploymentRepository
from app.repositories.incidents import IncidentRepository


def test_build_complete_evidence_package():

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

    current = Incident(
        id="CURRENT-001",
        service="payment-api",
        severity="SEV-1",
        diagnosis_status="investigating",
        timestamp="2026-10-06T09:17:00",
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

    retrieved = retriever.retrieve(
        current,
        top_k=3,
    )

    deployments = correlator.correlate(
        current
    )

    builder = EvidenceBuilder()

    evidence = builder.build(
        retrieved_incidents=retrieved,
        deployment_correlations=deployments,
    )

    print("\n=== INCIDENT EVIDENCE ===")

    for item in evidence.incident_evidence:
        print(
            f"{item.incident_id} | "
            f"similarity={item.similarity_score:.3f} | "
            f"status={item.diagnosis_status} | "
            f"root_cause={item.root_cause}"
        )

    print("\n=== DEPLOYMENT EVIDENCE ===")

    for item in evidence.deployment_evidence:
        print(
            f"{item.deployment_id} | "
            f"version={item.version} | "
            f"delta={item.incident_time_delta} | "
            f"status={item.status}"
        )

    assert len(evidence.incident_evidence) == 3

    assert len(evidence.deployment_evidence) > 0

    assert any(
        item.version == "2.14.3"
        for item in evidence.deployment_evidence
    )