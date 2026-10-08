import pytest
from app.core.retrieval import IncidentRetriever
from app.models.schemas import Incident
from app.repositories.incidents import IncidentRepository


@pytest.fixture
def retriever():
    repository = IncidentRepository("acmepay_dataset/incidents.json")
    return IncidentRetriever(repository)


RETRIEVAL_CASES = [
    {
        "name": "connection_pool_exhaustion",
        "current": Incident(
            id="CURRENT-POOL",
            service="payment-api",
            severity="SEV-1",
            diagnosis_status="investigating",
            timestamp="2026-10-06T09:17:00",
            category="connection_pool_exhaustion",
            title="Payment API elevated 5xx errors",
            symptoms=["HTTP 5xx", "database connection timeouts"],
            root_cause="Unknown",
            resolution=[],
            recent_deployment="2.14.3",
        ),
        "top_k": 3,
        "expected_top1": "INC-0500",
        "expected_in_topk": {"INC-0500", "INC-0510"},
    },
]


@pytest.mark.parametrize(
    "case",
    RETRIEVAL_CASES,
    ids=[c["name"] for c in RETRIEVAL_CASES],
)
def test_retrieval_quality(retriever, case):
    results = retriever.retrieve(case["current"], top_k=case["top_k"])
    retrieved_ids = {r.incident.id for r in results}

    assert len(results) == case["top_k"]

    assert results[0].incident.id == case["expected_top1"]

    assert case["expected_in_topk"] <= retrieved_ids, (
        f"Missing {case['expected_in_topk'] - retrieved_ids} "
        f"in retrieved results, got {retrieved_ids}"
    )