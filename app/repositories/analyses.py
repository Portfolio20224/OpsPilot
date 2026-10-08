import json
from pathlib import Path

from datetime import datetime

from app.models.audit import AnalysisRecord, ValidationStatus


class AnalysisRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def save(self, analysis: AnalysisRecord) -> None:
        analyses = self._load()

        analyses.append(
            analysis.model_dump(mode="json")
        )

        self.path.write_text(
            json.dumps(
                analyses,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def get_by_request_id(
        self,
        request_id: str,
    ) -> AnalysisRecord | None:
        analyses = self._load()

        for analysis in analyses:
            if analysis["request_id"] == request_id:
                return AnalysisRecord.model_validate(analysis)

        return None

    def get_by_incident_id(
            self, 
            incident_id: str
    ) -> list[AnalysisRecord]:
        analyses = self._load()

        results = [
            AnalysisRecord.model_validate(analysis)
            for analysis in analyses
            if analysis["incident_id"] == incident_id
        ]

        results.sort(
            key=lambda analysis: analysis.created_at,
            reverse=True,
        )

        return results

    def _load(self) -> list[dict]:
        content = self.path.read_text(
            encoding="utf-8"
        )

        return json.loads(content)
    
    def update_validation(
        self,
        request_id: str,
        validation_status: ValidationStatus,
        validated_by: str,
        validation_comment: str | None = None,
    ) -> AnalysisRecord | None:
        analyses = self._load()

        for analysis in analyses:
            if analysis["request_id"] != request_id:
                continue

            record = AnalysisRecord.model_validate(analysis)

            record.validation_status = validation_status
            record.validated_at = datetime.now().astimezone()
            record.validated_by = validated_by
            record.validation_comment = validation_comment

            analysis.clear()
            analysis.update(record.model_dump(mode="json"))

            self.path.write_text(
                json.dumps(
                    analyses,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            return record

        return None