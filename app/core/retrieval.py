import re

from app.models.schemas import Incident, RetrievedIncident
from app.repositories.incidents import IncidentRepository



class IncidentRetriever:
    def __init__(self, repository: IncidentRepository):
        self.repository = repository

    def retrieve(
        self,
        current: Incident,
        top_k: int = 5,
    ) -> list[RetrievedIncident]:

        candidates = self.repository.get_by_service(
            current.service
        )

        scored = [
            RetrievedIncident(
                incident=candidate,
                score=self._score(current, candidate),
            )
            for candidate in candidates
            if candidate.id != current.id
        ]

        scored.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return scored[:top_k]

    def _score(
        self,
        current: Incident,
        candidate: Incident,
    ) -> float:

        score = 0.0

        if current.service == candidate.service:
            score += 0.2

        if current.category == candidate.category:
            score += 0.3

        current_symptoms = {
            self._normalize_phrase(symptom)
            for symptom in current.symptoms
        }

        candidate_symptoms = {
            self._normalize_phrase(symptom)
            for symptom in candidate.symptoms
        }

        if current_symptoms:
            overlap = (
                len(current_symptoms & candidate_symptoms)
                / len(current_symptoms)
            )

            score += 0.3 * overlap

        title_similarity = self._title_similarity(
            current.title,
            candidate.title,
        )

        score += 0.2 * title_similarity

        return min(score, 1.0)

    @staticmethod
    def _normalize_phrase(text: str) -> str:
        return " ".join(
            re.findall(
                r"\b[a-zA-Z0-9]+\b",
                text.lower(),
            )
        )

    def _title_similarity(
        self,
        title_a: str,
        title_b: str,
    ) -> float:

        words_a = set(
            self._normalize_phrase(title_a).split()
        )

        words_b = set(
            self._normalize_phrase(title_b).split()
        )

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return len(intersection) / len(union)