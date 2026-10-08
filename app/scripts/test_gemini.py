from dotenv import load_dotenv
load_dotenv()
from datetime import timedelta

from app.models.schemas import (
    DeploymentEvidence,
    EvidencePackage,
    IncidentEvidence,
)
from app.core.reasoning import create_gemini_reasoner


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

reasoner = create_gemini_reasoner()

diagnosis = reasoner.diagnose(evidence)

print("=== DIAGNOSIS ===")
print(f"Root cause: {diagnosis.root_cause}")
print(f"Confidence: {diagnosis.confidence}")
print(f"Reasoning: {diagnosis.reasoning}")