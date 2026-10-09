import os
from statistics import median

import requests
import streamlit as st

API_URL = os.getenv(
    "OPSPILOT_API_URL",
    "http://localhost:8000",
).rstrip("/")


st.set_page_config(
    page_title="OpsPilot Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("OpsPilot — Operations Dashboard")
st.caption(
    "Incident analysis, deployment correlations and human validation."
)

if st.button("Refresh data"):
    st.rerun()


@st.cache_data(ttl=15)
def fetch_analyses(api_url: str) -> list[dict]:
    response = requests.get(
        f"{api_url}/analyses",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


try:
    analyses = fetch_analyses(API_URL)
except requests.RequestException as exc:
    st.error(
        "Unable to load analyses from the API. "
        "Check that the backend is running."
    )
    st.caption(f"Technical detail: {exc}")
    st.stop()


if not analyses:
    st.info(
        "No analyses yet. Run an incident analysis to populate the dashboard."
    )
    st.metric("Total analyses", 0)
    st.stop()


durations = [
    float(analysis["total_duration_ms"])
    for analysis in analyses
    if analysis.get("total_duration_ms") is not None
]

correlated_count = sum(
    analysis.get("deployment_correlation_count", 0) > 0
    for analysis in analyses
)

approved_count = sum(
    analysis.get("validation_status") == "approved"
    for analysis in analyses
)
rejected_count = sum(
    analysis.get("validation_status") == "rejected"
    for analysis in analyses
)
decided_count = approved_count + rejected_count

approval_rate = (
    approved_count / decided_count * 100
    if decided_count
    else None
)

pending_count = sum(
    analysis.get("validation_status", "pending") == "pending"
    for analysis in analyses
)

col1, col2, col3 = st.columns(3)

col1.metric("Total analyses", len(analyses))
col2.metric(
    "Median analysis duration",
    f"{median(durations):.0f} ms" if durations else "N/A",
)
col3.metric(
    "P95 analysis duration",
    (
        f"{sorted(durations)[min(int(0.95 * (len(durations) - 1)), len(durations) - 1)]:.0f} ms"
        if durations
        else "N/A"
    ),
)

col4, col5, col6 = st.columns(3)

col4.metric(
    "Deployment correlation rate",
    f"{correlated_count / len(analyses) * 100:.1f}%",
)
col5.metric(
    "Human approval rate",
    f"{approval_rate:.1f}%" if approval_rate is not None else "N/A",
)
col6.metric("Pending validations", pending_count)

st.divider()

st.subheader("Recent analyses")

for analysis in analyses[:10]:
    diagnosis = analysis.get("diagnosis") or {}
    confidence = diagnosis.get("confidence")

    with st.expander(
        f"{analysis.get('incident_id', 'Unknown incident')} "
        f"— {analysis.get('status', 'unknown status')}"
    ):
        st.write(f"**Request ID:** {analysis.get('request_id', 'N/A')}")
        st.write(f"**Service:** {analysis.get('service') or 'Unknown'}")
        st.write(f"**Severity:** {analysis.get('severity') or 'Unknown'}")
        st.write(
            "**Validation:** "
            f"{analysis.get('validation_status', 'pending')}"
        )
        st.write(
            "**Diagnosis confidence:** "
            f"{f'{confidence:.0%}' if confidence is not None else 'N/A'}"
        )
        st.write(
            "**Similar incidents retrieved:** "
            f"{analysis.get('retrieved_incident_count', 0)}"
        )
        st.write(
            "**Deployment correlations:** "
            f"{analysis.get('deployment_correlation_count', 0)}"
        )

st.caption(
    "A temporal correlation with a deployment does not prove causality. "
    "Approval rate excludes analyses that are still pending."
)