import os
from datetime import date, datetime, timedelta

import pandas as pd
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


@st.cache_data(ttl=15)
def fetch_analyses(api_url: str) -> list[dict]:
    response = requests.get(f"{api_url}/analyses", timeout=10)
    response.raise_for_status()
    return response.json()


def build_filters(
    service: str,
    severity: str,
    start_date: date,
    end_date: date,
) -> dict:
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    if service != "All":
        params["service"] = service

    if severity != "All":
        params["severity"] = severity

    return params


@st.cache_data(ttl=15)
def fetch_filtered_analyses(
    api_url: str,
    filters: dict,
) -> list[dict]:
    response = requests.get(
        f"{api_url}/analyses",
        params=filters,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=15)
def fetch_metrics(api_url: str, filters: dict) -> dict:
    response = requests.get(
        f"{api_url}/analyses/dashboard/metrics",
        params=filters,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()


try:
    all_analyses = fetch_analyses(API_URL)
except requests.RequestException:
    st.error("Unable to load analyses. Check that the API is running.")
    st.stop()


if not all_analyses:
    st.info("No analyses yet. Run an incident analysis first.")
    st.metric("Total analyses", 0)
    st.stop()


# Build filter options from the available history.
services = sorted({
    a["service"]
    for a in all_analyses
    if a.get("service")
})

severities = sorted({
    a["severity"]
    for a in all_analyses
    if a.get("severity")
})

created_dates = []

for analysis in all_analyses:
    value = analysis.get("created_at")
    if value:
        try:
            created_dates.append(
                datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).date()
            )
        except ValueError:
            pass

today = date.today()
default_start = min(created_dates) if created_dates else today
default_end = max(max(created_dates), today) if created_dates else today

st.subheader("Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    selected_service = st.selectbox(
        "Service",
        ["All", *services],
    )

with filter_col2:
    selected_severity = st.selectbox(
        "Severity",
        ["All", *severities],
    )

with filter_col3:
    selected_dates = st.date_input(
        "Analysis period",
        value=(default_start, default_end),
    )

if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
    st.warning("Select both a start date and an end date.")
    st.stop()

start_date, end_date = selected_dates

if start_date > end_date:
    st.error("The start date must be before the end date.")
    st.stop()

filters = build_filters(
    selected_service,
    selected_severity,
    start_date,
    end_date,
)

try:
    analyses = fetch_filtered_analyses(API_URL, filters)
    metrics = fetch_metrics(API_URL, filters)
except requests.RequestException:
    st.error("Unable to load filtered data from the API.")
    st.stop()


# KPI cards — all metrics are calculated by the backend.
st.subheader("Operational KPIs")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total analyses",
    metrics["analysis_count"],
)

median_duration = metrics.get("median_duration_ms")
col2.metric(
    "Median analysis duration",
    f"{median_duration:.0f} ms" if median_duration is not None else "N/A",
)

p95_duration = metrics.get("p95_duration_ms")
col3.metric(
    "P95 analysis duration",
    f"{p95_duration:.0f} ms" if p95_duration is not None else "N/A",
    help="95th percentile of total analysis duration.",
)

col4, col5, col6 = st.columns(3)

correlation_rate = metrics.get("deployment_correlation_rate")
col4.metric(
    "Deployment correlation rate",
    f"{correlation_rate:.1%}" if correlation_rate is not None else "N/A",
    help="Percentage of analyses with at least one deployment correlation. Correlation does not prove causality.",
)

approval_rate = metrics.get("approval_rate")
col5.metric(
    "Human approval rate",
    f"{approval_rate:.1%}" if approval_rate is not None else "N/A",
    help="Approvals divided by approvals plus rejections. Pending analyses are excluded.",
)

col6.metric(
    "Pending validations",
    metrics["pending_count"],
)

col7, col8, col9 = st.columns(3)

average_similar = metrics.get("average_similar_incidents")
col7.metric(
    "Avg. similar incidents",
    f"{average_similar:.1f}" if average_similar is not None else "N/A",
)

human_coverage = metrics.get("human_coverage_rate")
col8.metric(
    "Human validation coverage",
    f"{human_coverage:.1%}" if human_coverage is not None else "N/A",
)

average_confidence = metrics.get("average_confidence")
col9.metric(
    "Average diagnosis confidence",
    f"{average_confidence:.1%}" if average_confidence is not None else "N/A",
)

st.divider()

# Charts
st.subheader("Analysis performance")

if analyses:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Analysis duration by incident**")

        duration_rows = [
            {
                "Incident": a.get("incident_id", "Unknown"),
                "Duration (ms)": a.get("total_duration_ms"),
            }
            for a in analyses
            if a.get("total_duration_ms") is not None
        ]

        if duration_rows:
            duration_df = pd.DataFrame(duration_rows)
            st.bar_chart(
                duration_df.set_index("Incident")["Duration (ms)"]
            )
        else:
            st.info("No duration measurements available.")

    with chart_col2:
        st.markdown("**Human validation status**")

        status_counts = {
            "Approved": 0,
            "Rejected": 0,
            "Pending": 0,
        }

        for analysis in analyses:
            status = analysis.get("validation_status", "pending")
            if status == "approved":
                status_counts["Approved"] += 1
            elif status == "rejected":
                status_counts["Rejected"] += 1
            else:
                status_counts["Pending"] += 1

        status_df = pd.DataFrame(
            {
                "Status": list(status_counts.keys()),
                "Analyses": list(status_counts.values()),
            }
        )

        st.bar_chart(status_df.set_index("Status"))

else:
    st.info("No analyses match the selected filters.")

st.divider()

# Recent analyses
st.subheader("Analyses matching the filters")

if analyses:
    for analysis in analyses[:20]:
        diagnosis = analysis.get("diagnosis") or {}
        confidence = diagnosis.get("confidence")
        incident_id = analysis.get("incident_id", "Unknown")
        status = analysis.get("status", "unknown")

        with st.expander(f"{incident_id} — {status}"):
            st.write(f"**Request ID:** {analysis.get('request_id', 'N/A')}")
            st.write(f"**Service:** {analysis.get('service') or 'Unknown'}")
            st.write(f"**Severity:** {analysis.get('severity') or 'Unknown'}")
            st.write(
                f"**Validation:** {analysis.get('validation_status', 'pending')}"
            )
            st.write(
                "**Diagnosis confidence:** "
                + (f"{confidence:.1%}" if confidence is not None else "N/A")
            )
            st.write(
                f"**Similar incidents:** {analysis.get('retrieved_incident_count', 0)}"
            )
            st.write(
                f"**Deployment correlations:** "
                f"{analysis.get('deployment_correlation_count', 0)}"
            )

st.caption(
    "Deployment correlation is temporal evidence, not proof of causality. "
    "Approval rate excludes pending validations. "
    "These metrics describe recorded analyses; they do not establish time saved versus manual investigation."
)