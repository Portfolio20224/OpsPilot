from app.models.schemas import Severity
from app.repositories.incidents import IncidentRepository


def test_load_incidents():
    repository = IncidentRepository("acmepay_dataset/incidents.json")

    incidents = repository.get_all()

    assert len(incidents) > 0


def test_get_incident_by_id():
    repository = IncidentRepository("acmepay_dataset/incidents.json")

    incident = repository.get_by_id("INC-0500")

    assert incident is not None
    assert incident.id == "INC-0500"
    assert incident.service == "payment-api"


def test_get_incidents_by_service():
    repository = IncidentRepository("acmepay_dataset/incidents.json")

    incidents = repository.get_by_service("payment-api")

    assert len(incidents) > 0

    assert all(
        incident.service == "payment-api"
        for incident in incidents
    )


def test_get_incidents_by_severity():
    repository = IncidentRepository("acmepay_dataset/incidents.json")

    incidents = repository.get_by_severity(Severity.SEV_1)

    assert len(incidents) > 0

    assert all(
        incident.severity == Severity.SEV_1
        for incident in incidents
    )