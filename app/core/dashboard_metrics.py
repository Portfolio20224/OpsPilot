from statistics import mean, median
from typing import Any

from app.models.audit import AnalysisRecord, ValidationStatus


def percentile(values: list[float], percentile_value: float) -> float | None:
    """Calculate a percentile using linear interpolation."""
    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return (
        ordered[lower]
        + fraction * (ordered[upper] - ordered[lower])
    )


def calculate_dashboard_metrics(
    analyses: list[AnalysisRecord],
) -> dict[str, Any]:
    total_count = len(analyses)

    durations = [
        float(analysis.total_duration_ms)
        for analysis in analyses
        if analysis.total_duration_ms is not None
    ]

    similar_incident_counts = [
        analysis.retrieved_incident_count
        for analysis in analyses
    ]

    correlated_analyses = sum(
        analysis.deployment_correlation_count > 0
        for analysis in analyses
    )

    approved = sum(
        analysis.validation_status == ValidationStatus.APPROVED
        for analysis in analyses
    )
    rejected = sum(
        analysis.validation_status == ValidationStatus.REJECTED
        for analysis in analyses
    )
    pending = sum(
        analysis.validation_status == ValidationStatus.PENDING
        for analysis in analyses
    )

    decided_count = approved + rejected
    validated_analyses = [
        analysis
        for analysis in analyses
        if analysis.validation_status
        in (ValidationStatus.APPROVED, ValidationStatus.REJECTED)
        and analysis.validated_at is not None
    ]

    validation_delays_minutes = [
        (
            analysis.validated_at - analysis.created_at
        ).total_seconds() / 60
        for analysis in validated_analyses
        if analysis.validated_at is not None
        and analysis.validated_at >= analysis.created_at
    ]

    confidence_scores = [
        analysis.diagnosis.confidence
        for analysis in analyses
        if analysis.diagnosis is not None
    ]

    return {
        "analysis_count": total_count,
        "median_duration_ms": median(durations) if durations else None,
        "p95_duration_ms": percentile(durations, 0.95),
        "average_similar_incidents": (
            mean(similar_incident_counts)
            if similar_incident_counts
            else None
        ),
        "deployment_correlation_rate": (
            correlated_analyses / total_count
            if total_count
            else None
        ),
        "approval_rate": approved / decided_count if decided_count else None,
        "pending_count": pending,
        "human_coverage_rate": (
            len(validated_analyses) / total_count
            if total_count
            else None
        ),
        "median_validation_delay_minutes": (
            median(validation_delays_minutes)
            if validation_delays_minutes
            else None
        ),
        "average_confidence": (
            mean(confidence_scores)
            if confidence_scores
            else None
        ),
    }