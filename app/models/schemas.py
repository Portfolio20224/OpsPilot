from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from dataclasses import dataclass


class Severity(str, Enum):
    SEV_1 = "SEV-1"
    SEV_2 = "SEV-2"
    SEV_3 = "SEV-3"
    SEV_4 = "SEV-4"


class DiagnosisStatus(str, Enum):
    CONFIRMED = "confirmed"
    UNKNOWN = "unknown"
    INVESTIGATING = "investigating"

class IncidentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    service: str
    severity: Severity
    timestamp: datetime
    category: str
    title: str
    symptoms: list[str]
    recent_deployment: str | None = None

class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    service: str
    severity: Severity
    diagnosis_status: DiagnosisStatus 
    timestamp: datetime
    category: str
    title: str
    symptoms: list[str]
    root_cause: str
    resolution: list[str]
    recent_deployment: str | None = None


class Deployment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    service: str
    version: str
    previous_version: str | None = None
    deployed_at: datetime
    status: str


@dataclass
class RetrievedIncident:
    incident: Incident
    score: float

@dataclass
class DeploymentCorrelation:
    deployment: Deployment
    time_delta: timedelta


@dataclass
class IncidentEvidence:
    incident_id: str
    similarity_score: float
    diagnosis_status: str
    service: str
    category: str
    symptoms: list[str]
    root_cause: str
    resolution: list[str]
    recent_deployment: str | None


@dataclass
class DeploymentEvidence:
    deployment_id: str
    service: str
    version: str
    previous_version: str | None
    deployed_at: str
    incident_time_delta: timedelta
    status: str


@dataclass
class EvidencePackage:
    incident_evidence: list[IncidentEvidence]
    deployment_evidence: list[DeploymentEvidence]

class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    rationale: str
    priority: int = Field(ge=1, le=5)
    evidence_ids: list[str] = Field(default_factory=list)


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class IncidentState(BaseModel):
    incident: Incident

    retrieved_incidents: list[RetrievedIncident] = Field(
        default_factory=list
    )

    deployment_correlations: list[DeploymentCorrelation] = Field(
        default_factory=list
    )

    evidence: EvidencePackage | None = None

    diagnosis: Diagnosis | None = None

    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list
    )


    retrieval_duration_ms: float | None = None
    correlation_duration_ms: float | None = None
    evidence_duration_ms: float | None = None
    llm_duration_ms: float | None = None
    recommendation_duration_ms: float | None = None
    total_duration_ms: float | None = None


    evidence_ids: list[str] = Field(
        default_factory=list
    )

    status: str = "investigating"

    