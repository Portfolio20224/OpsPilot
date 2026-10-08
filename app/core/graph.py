import time
from langgraph.graph import StateGraph, START, END

from app.core.correlation import DeploymentCorrelator
from app.core.evidence import EvidenceBuilder
from app.core.retrieval import IncidentRetriever
from app.core.reasoning import IncidentReasoner
from app.models.schemas import IncidentState
from app.core.recommendations import RecommendationEngine

DIAGNOSIS_CONFIDENCE_THRESHOLD = 0.8

class IncidentGraph:
    def __init__(
        self,
        retriever: IncidentRetriever,
        correlator: DeploymentCorrelator,
        evidence_builder: EvidenceBuilder,
        reasoner: IncidentReasoner,
        recommendation_engine: RecommendationEngine,
    ):
        self.retriever = retriever
        self.correlator = correlator
        self.evidence_builder = evidence_builder
        self.reasoner = reasoner
        self.recommendation_engine = recommendation_engine

    def retrieve_incidents(self, state: IncidentState):
        start = time.perf_counter()
        results = self.retriever.retrieve(
            state.incident,
            top_k=3,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        return {
            "retrieved_incidents": results,
            "retrieval_duration_ms": duration_ms,
        }

    def correlate_deployments(self, state: IncidentState):
        start = time.perf_counter()
        correlations = self.correlator.correlate(
            state.incident
        )
        duration_ms = (time.perf_counter() - start) * 1000
        return {
            "deployment_correlations": correlations,
            "correlation_duration_ms": duration_ms,    
        }

    def build_evidence(self, state: IncidentState):

        start = time.perf_counter()
        evidence = self.evidence_builder.build(
            retrieved_incidents=state.retrieved_incidents,
            deployment_correlations=state.deployment_correlations,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        return {
            "evidence": evidence,
            "evidence_duration_ms": duration_ms,
        }

    def reason_with_llm(self, state: IncidentState):
        if state.evidence is None:
            raise ValueError("Evidence is required before reasoning")
        
        start = time.perf_counter()

        diagnosis = self.reasoner.diagnose(
            state.evidence
        )
        duration_ms = (time.perf_counter() - start) * 1000

        return {
            "diagnosis": diagnosis,
            "llm_duration_ms": duration_ms,
            "status": "diagnosed",
        }

    def validate_diagnosis(self, state: IncidentState):
        if state.diagnosis is None:
            raise ValueError(
                "Diagnosis is required before validation"
            )

        if (
            state.diagnosis.confidence
            >= DIAGNOSIS_CONFIDENCE_THRESHOLD
        ):
            return {
                "status": "diagnosis_validated",
            }

        return {
            "status": "human_validation_required",
        }
    
    def route_after_validation(self, state: IncidentState):
        if state.status == "diagnosis_validated":
            return "recommend_actions"

        return "human_validation"
    
    def recommend_actions(self, state: IncidentState):
        if state.diagnosis is None:
            raise ValueError(
                "Diagnosis is required before recommendations"
            )

        if state.evidence is None:
            raise ValueError(
                "Evidence is required before recommendations"
            )
        
        start = time.perf_counter()

        actions = self.recommendation_engine.recommend(
            diagnosis=state.diagnosis,
            evidence=state.evidence,
        )

        duration_ms = (time.perf_counter() - start) * 1000

        return {
            "recommended_actions": actions,
            "recommendation_duration_ms": duration_ms,
            "status": "recommendations_ready",
        }


    def human_validation(self, state: IncidentState):
        return {
            "status": "human_validation_required",
        }
    
    def build(self):
        graph = StateGraph(IncidentState)

        graph.add_node(
            "retrieve_incidents",
            self.retrieve_incidents,
        )

        graph.add_node(
            "correlate_deployments",
            self.correlate_deployments,
        )

        graph.add_node(
            "build_evidence",
            self.build_evidence,
        )

        graph.add_node(
            "reason_with_llm",
            self.reason_with_llm,
        )

        graph.add_node(
            "validate_diagnosis",
            self.validate_diagnosis,
        )

        graph.add_node(
            "recommend_actions",
            self.recommend_actions,
        )

        graph.add_node(
            "human_validation",
            self.human_validation,
        )

        graph.add_edge(
            START,
            "retrieve_incidents",
        )

        graph.add_edge(
            "retrieve_incidents",
            "correlate_deployments",
        )

        graph.add_edge(
            "correlate_deployments",
            "build_evidence",
        )

        graph.add_edge(
            "build_evidence",
            "reason_with_llm",
        )

        graph.add_edge(
            "reason_with_llm",
            "validate_diagnosis",
        )

        graph.add_conditional_edges(
            "validate_diagnosis",
            self.route_after_validation,
            {
                "recommend_actions": "recommend_actions",
                "human_validation": "human_validation",
            },
        )

        graph.add_edge(
            "recommend_actions",
            END,
        )

        graph.add_edge(
            "human_validation",
            END,
        )

        return graph.compile()