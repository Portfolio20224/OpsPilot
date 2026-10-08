from app.models.schemas import DeploymentCorrelation, EvidencePackage, IncidentEvidence, DeploymentEvidence, RetrievedIncident




class EvidenceBuilder:

    def build(
        self,
        retrieved_incidents: list[RetrievedIncident],
        deployment_correlations: list[DeploymentCorrelation],
    ) -> EvidencePackage:

        incident_evidence = [
            IncidentEvidence(
                incident_id=result.incident.id,
                similarity_score=result.score,
                diagnosis_status=result.incident.diagnosis_status.value,
                service=result.incident.service,
                category=result.incident.category,
                symptoms=result.incident.symptoms,
                root_cause=result.incident.root_cause,
                resolution=result.incident.resolution,
                recent_deployment=result.incident.recent_deployment,
            )
            for result in retrieved_incidents
        ]

        deployment_evidence = [
            DeploymentEvidence(
                deployment_id=result.deployment.id,
                service=result.deployment.service,
                version=result.deployment.version,
                previous_version=result.deployment.previous_version,
                deployed_at=result.deployment.deployed_at.isoformat(),
                incident_time_delta=result.time_delta,
                status=result.deployment.status,
            )
            for result in deployment_correlations
        ]

        return EvidencePackage(
            incident_evidence=incident_evidence,
            deployment_evidence=deployment_evidence,
        )