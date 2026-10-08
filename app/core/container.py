from app.core.correlation import DeploymentCorrelator
from app.core.evidence import EvidenceBuilder
from app.core.graph import IncidentGraph
from app.core.recommendations import RecommendationEngine
from app.core.reasoning import create_gemini_reasoner
from app.core.retrieval import IncidentRetriever
from app.repositories.deployments import DeploymentRepository
from app.repositories.incidents import IncidentRepository
from app.repositories.analyses import AnalysisRepository
from app.core.config import settings

def create_analysis_repository() -> AnalysisRepository:
    return AnalysisRepository(
        settings.analysis_history_path
    )

def create_incident_graph() -> IncidentGraph:
    incident_repository = IncidentRepository(
        settings.incident_data_path
    )

    deployment_repository = DeploymentRepository(
        settings.deployment_data_path
    )

    retriever = IncidentRetriever(
        incident_repository
    )

    correlator = DeploymentCorrelator(
        deployment_repository,
        max_minutes=60,
    )

    evidence_builder = EvidenceBuilder()

    reasoner = create_gemini_reasoner()

    recommendation_engine = RecommendationEngine()

    return IncidentGraph(
        retriever=retriever,
        correlator=correlator,
        evidence_builder=evidence_builder,
        reasoner=reasoner,
        recommendation_engine=recommendation_engine,
    ).build()