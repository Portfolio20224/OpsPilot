import json
from pathlib import Path

from app.models.schemas import Incident, Severity


class IncidentRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._incidents = self._load()

    def _load(self) -> list[Incident]:
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return [Incident.model_validate(item) for item in data]

    def get_all(self) -> list[Incident]:
        return self._incidents

    def get_by_id(self, incident_id: str) -> Incident | None:
        for incident in self._incidents:
            if incident.id == incident_id:
                return incident

        return None

    def get_by_service(self, service: str) -> list[Incident]:
        return [
            incident
            for incident in self._incidents
            if incident.service == service
        ]

    def get_by_severity(self, severity: Severity) -> list[Incident]:
        return [
            incident
            for incident in self._incidents
            if incident.severity == severity
        ]