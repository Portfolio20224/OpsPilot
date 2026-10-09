from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models.schemas import Diagnosis, EvidencePackage, RecommendedAction


class ValidationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AnalysisRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    incident_id: str
    created_at: datetime

    status: str
    diagnosis: Diagnosis | None = None
    recommended_actions: list[RecommendedAction]
    evidence: EvidencePackage | None = None

    duration_ms: float | None = None

    validation_status: ValidationStatus = ValidationStatus.PENDING
    validated_at: datetime | None = None
    validated_by: str | None = None
    validation_comment: str | None = None

    retrieved_incident_count: int = 0
    deployment_correlation_count: int = 0
    llm_duration_ms: float | None = None
    total_duration_ms: float | None = None

    service: str | None = None
    severity: str | None = None

class ValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ValidationStatus
    validated_by: str
    comment: str | None = None