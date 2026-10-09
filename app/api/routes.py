import logging
from datetime import date, datetime, timezone
import time
logger = logging.getLogger("opspilot")
from fastapi import APIRouter, Depends, HTTPException
from functools import lru_cache
from app.core.container import (
    create_analysis_repository,
    create_incident_graph,
)
from app.models.audit import (
    AnalysisRecord,
    ValidationRequest,
    ValidationStatus,
)
from app.models.schemas import IncidentState, Incident, IncidentInput, DiagnosisStatus
from app.models.responses import IncidentAnalysisResponse
from app.core.exceptions import (
    LLMResponseError,
    LLMTimeoutError,
)
from app.core.observability import (
    generate_request_id,
    measure_operation,
)
from app.core.dashboard_metrics import calculate_dashboard_metrics

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)

analysis_router = APIRouter(
    prefix="/analyses", 
    tags=["analyses"]
)

def get_analysis_repository():
    return create_analysis_repository()

@lru_cache(maxsize=1)
def get_incident_graph():
    return create_incident_graph()


@router.post(
    "/analyze",
    response_model=IncidentAnalysisResponse,
)
def analyze_incident(
    incident_input: IncidentInput,
    graph=Depends(get_incident_graph),
    analysis_repository=Depends(get_analysis_repository),
):
    request_id = generate_request_id()

    incident = Incident(
        id=incident_input.id,
        service=incident_input.service,
        severity=incident_input.severity,
        diagnosis_status=DiagnosisStatus.INVESTIGATING,
        timestamp=incident_input.timestamp,
        category=incident_input.category,
        title=incident_input.title,
        symptoms=incident_input.symptoms,
        root_cause="Unknown",
        resolution=[],
        recent_deployment=incident_input.recent_deployment,
    )

    logger.info(
        "incident_analysis_started "
        "request_id=%s incident_id=%s service=%s",
        request_id,
        incident.id,
        incident.service,
    )
    started_at = time.perf_counter()

    try:
        with measure_operation(
            operation="incident_analysis",
            request_id=request_id,
        ):
            result = graph.invoke(
                {
                    "incident": incident,
                }
            )


    except LLMTimeoutError as exc:
        logger.error(
            "incident_analysis_failed "
            "request_id=%s incident_id=%s error=llm_timeout",
            request_id,
            incident.id,
        )

        raise HTTPException(
            status_code=504,
            detail="LLM request timed out",
        ) from exc

    except LLMResponseError as exc:
        logger.error(
            "incident_analysis_failed "
            "request_id=%s incident_id=%s error=llm_error",
            request_id,
            incident.id,
        )

        raise HTTPException(
            status_code=502,
            detail="LLM diagnosis failed",
        ) from exc
    duration_ms = (
        time.perf_counter() - started_at
    ) * 1000

    state = IncidentState.model_validate(result)
    state.total_duration_ms = duration_ms

    analysis = AnalysisRecord(
        request_id=request_id,
        incident_id=state.incident.id,
        created_at=datetime.now(timezone.utc),
        status=state.status,
        diagnosis=state.diagnosis,
        recommended_actions=state.recommended_actions,
        evidence=state.evidence,
        duration_ms=duration_ms,

        retrieved_incident_count=len(state.retrieved_incidents),
        deployment_correlation_count=len(
            state.deployment_correlations
        ),
        llm_duration_ms=state.llm_duration_ms,
        total_duration_ms=state.total_duration_ms,
        service=incident.service,
        severity=incident.severity.value,
    )

    analysis_repository.save(analysis)

    logger.info(
        "incident_analysis_completed "
        "request_id=%s incident_id=%s status=%s",
        request_id,
        incident.id,
        state.status,
    )

    return IncidentAnalysisResponse(
        request_id=request_id,
        incident_id=state.incident.id,
        status=state.status,
        diagnosis=state.diagnosis,
        recommended_actions=state.recommended_actions,
        evidence=state.evidence,

        retrieved_incident_count=len(state.retrieved_incidents),
        deployment_correlation_count=len(
            state.deployment_correlations
        ),
        llm_duration_ms=state.llm_duration_ms,
        total_duration_ms=state.total_duration_ms,
    )


@router.get(
    "/{incident_id}/analyses",
    response_model=list[AnalysisRecord],
)
def get_incident_analyses(
    incident_id: str,
    analysis_repository=Depends(get_analysis_repository),
):
    return analysis_repository.get_by_incident_id(incident_id)


@analysis_router.get(
    "",
    response_model=list[AnalysisRecord],
)
def get_all_analyses(
    service: str | None = None,
    severity: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    analysis_repository=Depends(get_analysis_repository),
) -> list[AnalysisRecord]:
    """Return analyses with optional filters, newest first."""
    analyses = analysis_repository.get_all()

    if service:
        analyses = [
            analysis
            for analysis in analyses
            if analysis.service == service
        ]

    if severity:
        analyses = [
            analysis
            for analysis in analyses
            if analysis.severity == severity
        ]

    if start_date:
        analyses = [
            analysis
            for analysis in analyses
            if analysis.created_at.date() >= start_date
        ]

    if end_date:
        analyses = [
            analysis
            for analysis in analyses
            if analysis.created_at.date() <= end_date
        ]

    return analyses


@analysis_router.get("/dashboard/metrics")
def get_dashboard_metrics(
    service: str | None = None,
    severity: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    analysis_repository=Depends(get_analysis_repository),
) -> dict:
    """Return dashboard metrics for the selected filters."""
    analyses = analysis_repository.get_all()

    if service:
        analyses = [
            a for a in analyses if a.service == service
        ]

    if severity:
        analyses = [
            a for a in analyses if a.severity == severity
        ]

    if start_date:
        analyses = [
            a for a in analyses
            if a.created_at.date() >= start_date
        ]

    if end_date:
        analyses = [
            a for a in analyses
            if a.created_at.date() <= end_date
        ]

    return calculate_dashboard_metrics(analyses)


@analysis_router.get(
    "/{request_id}",
    response_model=AnalysisRecord,
)
def get_analysis(
    request_id: str,
    analysis_repository=Depends(get_analysis_repository),
):
    analysis = analysis_repository.get_by_request_id(request_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return analysis

@analysis_router.post(
    "/{request_id}/validation",
    response_model=AnalysisRecord,
)
def validate_analysis(
    request_id: str,
    validation: ValidationRequest,
    analysis_repository=Depends(get_analysis_repository),
):
    analysis = analysis_repository.get_by_request_id(request_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    if analysis.validation_status != ValidationStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail="Analysis has already been validated",
        )

    updated_analysis = analysis_repository.update_validation(
        request_id=request_id,
        validation_status=validation.status,
        validated_by=validation.validated_by,
        validation_comment=validation.comment,
    )

    if updated_analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return updated_analysis