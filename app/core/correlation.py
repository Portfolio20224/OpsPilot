from datetime import timedelta

from app.models.schemas import DeploymentCorrelation, Incident
from app.repositories.deployments import DeploymentRepository





class DeploymentCorrelator:

    def __init__(
        self,
        repository: DeploymentRepository,
        max_minutes: int = 60,
    ):
        self.repository = repository
        self.max_delta = timedelta(minutes=max_minutes)

    def correlate(
        self,
        incident: Incident,
    ) -> list[DeploymentCorrelation]:

        deployments = self.repository.get_by_service(
            incident.service
        )

        correlations = []

        for deployment in deployments:

            delta = incident.timestamp - deployment.deployed_at

            if timedelta(0) <= delta <= self.max_delta:

                correlations.append(
                    DeploymentCorrelation(
                        deployment=deployment,
                        time_delta=delta,
                    )
                )

        correlations.sort(
            key=lambda result: result.time_delta
        )

        return correlations