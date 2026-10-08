import json
import re

from app.models.schemas import Diagnosis, EvidencePackage
from app.core.exceptions import (
    LLMResponseError,
    LLMTimeoutError,
)



class IncidentReasoner:
    def __init__(self, model):
        self.model = model


    def diagnose(self, evidence: EvidencePackage) -> Diagnosis:
        prompt = self._build_prompt(evidence)

        try:
            response = self.model.invoke(prompt)
        except TimeoutError as exc:
            raise LLMTimeoutError(
                "LLM request timed out"
            ) from exc
        except Exception as exc:
            raise LLMResponseError(
                "LLM request failed"
            ) from exc

        try:
            content = self._extract_text(response.content)
            payload = self._extract_json(content)
            return Diagnosis.model_validate(payload)

        except (TypeError, ValueError) as exc:
            raise LLMResponseError(
                "LLM returned an invalid diagnosis"
            ) from exc

    @staticmethod
    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_blocks = []

            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text")
                    if text:
                        text_blocks.append(text)

            return "\n".join(text_blocks)

        raise TypeError(
            f"Unsupported response content type: {type(content).__name__}"
        )

    @staticmethod
    def _extract_json(response: str) -> dict:
        if not response:
            raise ValueError("Empty LLM response")

        response = re.sub(
            r"^```(?:json)?\s*",
            "",
            response.strip(),
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"\s*```$",
            "",
            response,
        )

        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError(
                f"No JSON object found in LLM response: {response}"
            )

        json_content = response[start:end]

        try:
            return json.loads(json_content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON returned by LLM: {json_content}"
            ) from exc

    def _build_prompt(self, evidence: EvidencePackage) -> str:
        return f"""
You are an incident response assistant.

Analyze the incident using ONLY the evidence provided below.

## CRITICAL RULES

Do not invent facts.
Do not assume information that is not present in the evidence.

Your task is to determine:
1. The most likely root cause.
2. Your confidence between 0 and 1.
3. A concise reasoning explaining which evidence supports your diagnosis.

## EVIDENCE TO ANALYZE:

Historical incidents:
{evidence.incident_evidence}

Deployment evidence:
{evidence.deployment_evidence}

## OUTPUT
Return ONLY valid JSON with this structure:

{{
    "root_cause": "string",
    "confidence": 0.0,
    "reasoning": "string"
}}
## RESPONSE (JSON ONLY)"""

    
def create_gemini_reasoner() -> IncidentReasoner:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from app.core.config import settings
    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=0,
        timeout=30,
        max_retries=2,
    )

    return IncidentReasoner(model)