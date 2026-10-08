from app.core.correlation import DeploymentCorrelator
from app.models.schemas import Incident
from app.repositories.deployments import DeploymentRepository


def test_correlate_recent_deployment():

    repository = DeploymentRepository(
        "acmepay_dataset/deployments.json"
    )

    correlator = DeploymentCorrelator(
        repository,
        max_minutes=60,
    )

    incident = Incident(
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

    results = correlator.correlate(incident)

    assert len(results) > 0

    closest = results[0]

    assert closest.deployment.service == "payment-api"
    assert closest.deployment.version == "2.14.3"
    assert closest.time_delta.total_seconds() == 14 * 60