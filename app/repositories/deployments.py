from typing import List
import json
from pathlib import Path
from datetime import timedelta, datetime
from app.models.schemas import Deployment


class DeploymentRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._deployments = self._load()

    def _load(self) -> list[Deployment]:
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return [Deployment.model_validate(item) for item in data]

    def get_recent_deployments(self, service: str, before_time: datetime, window_minutes: int = 30) -> List[Deployment]:
        """Trouve les déploiements survenus juste avant l'incident."""
        window_start = before_time - timedelta(minutes=window_minutes)
        
        return [
            dep for dep in self._deployments 
            if dep.service == service and window_start <= dep.deployed_at <= before_time
        ]
    def get_all(self) -> list[Deployment]:
        return self._deployments

    def get_by_service(self, service: str) -> list[Deployment]:
        return [
            deployment
            for deployment in self._deployments
            if deployment.service == service
        ]

    def get_by_version(
        self,
        service: str,
        version: str,
    ) -> Deployment | None:

        for deployment in self._deployments:
            if (
                deployment.service == service
                and deployment.version == version
            ):
                return deployment

        return None