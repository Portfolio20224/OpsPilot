from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.audit import AnalysisRecord, ValidationStatus


class FakeAnalysisRepository:
    def __init__(self):
        self.analysis = AnalysisRecord(
            request_id="req-001",
            incident_id="INC-001",
            created_at=datetime.now(timezone.utc),
            status="recommendations_ready",
            diagnosis=None,
            recommended_actions=[],
            evidence=None,
            duration_ms=1250.5,
        )

    def get_by_request_id(self, request_id):
        if request_id == self.analysis.request_id:
            return self.analysis
        return None

    def get_by_incident_id(self, incident_id):
        if incident_id == self.analysis.incident_id:
            return [self.analysis]
        return []
    def update_validation(
        self,
        request_id,
        validation_status,
        validated_by,
        validation_comment = None,
    ):
        if request_id == self.analysis.request_id:
            self.analysis.validation_status = validation_status
            self.analysis.validated_by = validated_by
            self.analysis.validation_comment = validation_comment
            return self.analysis
        return None
    
class AlreadyValidatedRepository(FakeAnalysisRepository):
    def __init__(self):
        super().__init__()
        self.analysis.validation_status = ValidationStatus.APPROVED
    

    
def test_get_analysis_by_request_id():
    from app.api.routes import get_analysis_repository

    app.dependency_overrides[get_analysis_repository] = (
        lambda: FakeAnalysisRepository()
    )

    client = TestClient(app)

    response = client.get("/analyses/req-001")

    assert response.status_code == 200
    data = response.json()

    assert data["request_id"] == "req-001"
    assert data["incident_id"] == "INC-001"
    assert data["status"] == "recommendations_ready"

    app.dependency_overrides.clear()


def test_get_analysis_by_request_id_returns_404():
    from app.api.routes import get_analysis_repository

    app.dependency_overrides[get_analysis_repository] = (
        lambda: FakeAnalysisRepository()
    )

    client = TestClient(app)

    response = client.get("/analyses/unknown-request")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"

    app.dependency_overrides.clear()


def test_get_incident_analysis_history():
    from app.api.routes import get_analysis_repository

    app.dependency_overrides[get_analysis_repository] = (
        lambda: FakeAnalysisRepository()
    )

    client = TestClient(app)

    response = client.get("/incidents/INC-001/analyses")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["request_id"] == "req-001"
    assert data[0]["incident_id"] == "INC-001"

    app.dependency_overrides.clear()


def test_validate_analysis():
    from app.api.routes import get_analysis_repository

    app.dependency_overrides[get_analysis_repository] = (
        lambda: FakeAnalysisRepository()
    )

    client = TestClient(app)

    response = client.post(
        "/analyses/req-001/validation",
        json={
            "status": "approved",
            "validated_by": "operator-001",
            "comment": "Rollback approved after checking metrics.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"] == "req-001"
    assert data["validation_status"] == "approved"
    assert data["validated_by"] == "operator-001"
    assert (
        data["validation_comment"]
        == "Rollback approved after checking metrics."
    )

    app.dependency_overrides.clear()


def test_validate_unknown_analysis_returns_404():
    from app.api.routes import get_analysis_repository

    app.dependency_overrides[get_analysis_repository] = (
        lambda: FakeAnalysisRepository()
    )

    client = TestClient(app)

    response = client.post(
        "/analyses/unknown-request/validation",
        json={
            "status": "approved",
            "validated_by": "operator-001",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"

    app.dependency_overrides.clear()


def test_validate_already_validated_analysis_returns_409():
    from app.api.routes import get_analysis_repository

    app.dependency_overrides[get_analysis_repository] = (
        lambda: AlreadyValidatedRepository()
    )

    client = TestClient(app)

    response = client.post(
        "/analyses/req-001/validation",
        json={
            "status": "rejected",
            "validated_by": "operator-002",
            "comment": "Disagree with recommendation.",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Analysis has already been validated"
    )

    app.dependency_overrides.clear()