from datetime import timedelta

from app.models.schemas import (
    DeploymentEvidence,
    EvidencePackage,
    IncidentEvidence,
    Diagnosis,
)
from app.core.recommendations import RecommendationEngine


def test_recommendation_from_confirmed_historical_incidents():
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
                incident_id="INC-0510",
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
                    "Rolled back deployment 2.12.1"
                ],
                recent_deployment="2.12.1",
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

    diagnosis = Diagnosis(
        root_cause=(
            "Database connection pool exhaustion "
            "due to N+1 query in new release"
        ),
        confidence=0.94,
        reasoning="Confirmed historical incidents support the diagnosis.",
    )

    engine = RecommendationEngine()

    actions = engine.recommend(
        diagnosis=diagnosis,
        evidence=evidence,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action.action == "Roll back deployment 2.14.3"
    assert action.priority == 1

    assert "INC-0500" in action.evidence_ids
    assert "INC-0510" in action.evidence_ids
    assert "DEP-001" in action.evidence_ids