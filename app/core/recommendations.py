from app.models.schemas import Diagnosis, RecommendedAction, EvidencePackage


class RecommendationEngine:
    def recommend(
        self,
        diagnosis: Diagnosis,
        evidence: EvidencePackage,
    ) -> list[RecommendedAction]:
        actions = []

        if not self._has_confirmed_historical_evidence(evidence):
            return actions

        deployment = self._get_recent_deployment(evidence)

        if deployment is not None:
            historical_incidents = [
                incident
                for incident in evidence.incident_evidence
                if incident.diagnosis_status == "confirmed"
            ]

            evidence_ids = [
                incident.incident_id
                for incident in historical_incidents
            ]

            evidence_ids.append(deployment.deployment_id)

            actions.append(
                RecommendedAction(
                    action=f"Roll back deployment {deployment.version}",
                    rationale=(
                        "A deployment occurred shortly before the incident, "
                        "and confirmed historical incidents with the same "
                        "symptoms were resolved by rolling back the release."
                    ),
                    priority=1,
                    evidence_ids=evidence_ids,
                )
            )

        return actions

    @staticmethod
    def _has_confirmed_historical_evidence(
        evidence: EvidencePackage,
    ) -> bool:
        return any(
            incident.diagnosis_status == "confirmed"
            for incident in evidence.incident_evidence
        )

    @staticmethod
    def _get_recent_deployment(evidence: EvidencePackage):
        if not evidence.deployment_evidence:
            return None

        return min(
            evidence.deployment_evidence,
            key=lambda deployment: deployment.incident_time_delta,
        )