from pydantic import BaseModel, ConfigDict, Field

from app.models.schemas import Diagnosis, RecommendedAction, EvidencePackage


class IncidentAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    incident_id: str
    status: str
    diagnosis: Diagnosis | None = None
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list
    )
    evidence: EvidencePackage | None = None

    retrieved_incident_count: int = 0
    deployment_correlation_count: int = 0
    llm_duration_ms: float | None = None
    total_duration_ms: float | None = None