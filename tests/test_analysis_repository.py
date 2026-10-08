from datetime import datetime, timezone
from app.models.audit import AnalysisRecord, ValidationStatus
from app.repositories.analyses import AnalysisRepository


def test_analysis_repository_saves_and_loads(tmp_path):
    repository = AnalysisRepository(
        tmp_path / "analyses.json"
    )

    analysis = AnalysisRecord(
        request_id="req-001",
        incident_id="INC-001",
        created_at="2026-10-08T00:00:00Z",
        status="recommendations_ready",
        diagnosis=None,
        recommended_actions=[],
        evidence=None,
        duration_ms=1250.5,
    )

    repository.save(analysis)

    result = repository.get_by_request_id("req-001")

    assert result is not None
    assert result.request_id == "req-001"
    assert result.incident_id == "INC-001"
    assert result.status == "recommendations_ready"
    assert result.duration_ms == 1250.5


def test_analysis_repository_filters_by_incident(tmp_path):
    repository = AnalysisRepository(
        tmp_path / "analyses.json"
    )

    for request_id in ["req-001", "req-002"]:
        repository.save(
            AnalysisRecord(
                request_id=request_id,
                incident_id="INC-001",
                created_at="2026-10-08T00:00:00Z",
                status="recommendations_ready",
                diagnosis=None,
                recommended_actions=[],
                evidence=None,
            )
        )

    repository.save(
        AnalysisRecord(
            request_id="req-003",
            incident_id="INC-002",
            created_at="2026-10-08T00:00:00Z",
            status="recommendations_ready",
            diagnosis=None,
            recommended_actions=[],
            evidence=None,
        )
    )

    results = repository.get_by_incident_id("INC-001")

    assert len(results) == 2
    assert {item.request_id for item in results} == {
        "req-001",
        "req-002",
    }

def test_analysis_repository_returns_incident_history_newest_first(tmp_path):
    repository = AnalysisRepository(tmp_path / "analyses.json")

    repository.save(
        AnalysisRecord(
            request_id="req-old",
            incident_id="INC-001",
            created_at=datetime(
                2026, 10, 8, 10, 0, tzinfo=timezone.utc
            ),
            status="human_validation_required",
            diagnosis=None,
            recommended_actions=[],
            evidence=None,
        )
    )

    repository.save(
        AnalysisRecord(
            request_id="req-new",
            incident_id="INC-001",
            created_at=datetime(
                2026, 10, 8, 11, 0, tzinfo=timezone.utc
            ),
            status="recommendations_ready",
            diagnosis=None,
            recommended_actions=[],
            evidence=None,
        )
    )

    results = repository.get_by_incident_id("INC-001")

    assert len(results) == 2
    assert results[0].request_id == "req-new"
    assert results[1].request_id == "req-old"


def test_analysis_repository_updates_validation(tmp_path):
    repository = AnalysisRepository(tmp_path / "analyses.json")

    repository.save(
        AnalysisRecord(
            request_id="req-001",
            incident_id="INC-001",
            created_at="2026-10-08T10:00:00Z",
            status="recommendations_ready",
            diagnosis=None,
            recommended_actions=[],
            evidence=None,
        )
    )

    result = repository.update_validation(
        request_id="req-001",
        validation_status=ValidationStatus.APPROVED,
        validated_by="operator-001",
        validation_comment="Rollback approved after checking metrics.",
    )

    assert result is not None
    assert result.validation_status == ValidationStatus.APPROVED
    assert result.validated_by == "operator-001"
    assert (
        result.validation_comment
        == "Rollback approved after checking metrics."
    )
    assert result.validated_at is not None

    stored = repository.get_by_request_id("req-001")

    assert stored is not None
    assert stored.validation_status == ValidationStatus.APPROVED
    assert stored.validated_by == "operator-001"


def test_analysis_repository_returns_none_for_unknown_validation(tmp_path):
    repository = AnalysisRepository(tmp_path / "analyses.json")

    result = repository.update_validation(
        request_id="unknown-request",
        validation_status=ValidationStatus.REJECTED,
        validated_by="operator-001",
    )

    assert result is None