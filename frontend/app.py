import os
import requests
import streamlit as st


API_URL = os.getenv(
    "OPSPILOT_API_URL",
    "http://localhost:8000",
)


st.set_page_config(
    page_title="OpsPilot",
    page_icon="🚨",
    layout="wide",
)

def reset_analysis():
    keys_to_reset = [
        "analysis"
    ]

    for key in keys_to_reset:
        st.session_state.pop(key, None)

st.title("🚨 OpsPilot")
st.caption("AI-powered incident response assistant")

st.divider()

st.header("Incident")

col1, col2 = st.columns(2)

with col1:
    service = st.text_input(
        "Service",
        value="payment-api",
    )

with col2:
    severity = st.selectbox(
        "Severity",
        options=["SEV-1", "SEV-2", "SEV-3", "SEV-4"],
        index=0,
    )

title = st.text_input(
    "Title",
    value="Payment API elevated 5xx errors",
)

symptoms_text = st.text_area(
    "Symptoms",
    value="HTTP 5xx\ndatabase connection timeouts",
    help="One symptom per line.",
)

recent_deployment = st.text_input(
    "Recent deployment",
    value="2.14.3",
)

if st.button(
    "Analyze incident",
    type="primary",
    use_container_width=True,
):
    symptoms = [
        symptom.strip()
        for symptom in symptoms_text.splitlines()
        if symptom.strip()
    ]

    incident_input = {
        "id": "FRONTEND-001",
        "service": service,
        "severity": severity,
        "timestamp": "2026-10-08T12:00:00",
        "category": "connection_pool_exhaustion",
        "title": title,
        "symptoms": symptoms,
        "recent_deployment": recent_deployment or None,
    }

    with st.spinner("Analyzing incident..."):
        try:
            response = requests.post(
                f"{API_URL}/incidents/analyze",
                json=incident_input,
                timeout=60,
            )
        except requests.RequestException as exc:
            st.error(f"Unable to reach OpsPilot API: {exc}")
            st.stop()

    if response.status_code != 200:
        st.error(
            f"Analysis failed ({response.status_code}): "
            f"{response.text}"
        )
        st.stop()

    analysis = response.json()

    st.session_state["analysis"] = analysis

if "analysis" in st.session_state:
    analysis = st.session_state["analysis"]

    st.divider()

    st.header("Incident analysis")

    # ─────────────────────────────────────────────
    # Overview
    # ─────────────────────────────────────────────

    diagnosis = analysis.get("diagnosis")
    evidence = analysis.get("evidence")
    actions = analysis.get("recommended_actions", [])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Status",
            analysis.get("status", "unknown"),
        )

    with col2:
        if diagnosis:
            st.metric(
                "Confidence",
                f"{diagnosis['confidence']:.0%}",
            )
        else:
            st.metric("Confidence", "N/A")

    with col3:
        st.metric(
            "Historical incidents",
            analysis.get("retrieved_incident_count", 0),
        )

    with col4:
        st.metric(
            "Correlated deployments",
            analysis.get("deployment_correlation_count", 0),
        )

    total_duration = analysis.get("total_duration_ms")
    llm_duration = analysis.get("llm_duration_ms")

    if total_duration and llm_duration:
        llm_ratio = (llm_duration / total_duration) * 100

        st.caption(
            f"The LLM takes around {llm_ratio:.1f} % "
            "of the analysis's time."
        )

    # ─────────────────────────────────────────────
    # Diagnosis
    # ─────────────────────────────────────────────

    if diagnosis:
        st.subheader("🎯 Diagnosis")

        st.info(diagnosis["root_cause"])

        st.write("**Reasoning**")
        st.write(diagnosis["reasoning"])

    # ─────────────────────────────────────────────
    # Evidence
    # ─────────────────────────────────────────────

    if evidence:
        st.subheader("🔎 Evidence")

        tab_history, tab_deployments = st.tabs(
            [
                "Historical incidents",
                "Deployments",
            ]
        )

        with tab_history:
            for incident in evidence["incident_evidence"]:
                status = incident["diagnosis_status"]

                if status == "confirmed":
                    icon = "✅"
                elif status == "unknown":
                    icon = "⚠️"
                else:
                    icon = "❔"

                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(
                            f"{icon} **{incident['incident_id']}**"
                        )

                    with col2:
                        st.write(
                            f"Similarity: "
                            f"**{incident['similarity_score']:.3f}**"
                        )

                    with col3:
                        st.write(
                            f"Diagnosis: **{status}**"
                        )

                    st.write(
                        f"**Category:** "
                        f"{incident['category']}"
                    )

                    st.write(
                        f"**Symptoms:** "
                        f"{', '.join(incident['symptoms'])}"
                    )

                    st.write(
                        f"**Root cause:** "
                        f"{incident['root_cause']}"
                    )

        with tab_deployments:
            for deployment in evidence["deployment_evidence"]:
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(
                            f"🚀 **{deployment['deployment_id']}**"
                        )

                    with col2:
                        st.write(
                            f"Version: "
                            f"**{deployment['version']}**"
                        )

                    with col3:
                        st.write(
                            f"Status: "
                            f"**{deployment['status']}**"
                        )

                    st.write(
                        f"Time before incident: "
                        f"**{deployment['incident_time_delta']}**"
                    )

        st.subheader("⏱️ Incident timeline")

        if evidence["deployment_evidence"]:
            deployment = evidence["deployment_evidence"][0]

            st.write(
                f"🚀 **Deployment {deployment['deployment_id']}**"
            )

            st.caption(
                f"Version {deployment['version']} · "
                f"Status: {deployment['status']}"
            )

            st.write("⬇️")

            st.info(
                f"Incident detected "
                f"**{deployment['incident_time_delta']}** "
                f"after the deployment."
            )

            st.write("⬇️")

            st.error(
                f"🚨 **{analysis['incident_id']}** — "
                f"{service} incident"
            )

            st.caption(
                "Temporal correlation only — "
                "this does not prove causality."
            )
        else:
            st.info(
                "No deployment was correlated with this incident."
            )

    # ─────────────────────────────────────────────
    # Recommendation
    # ─────────────────────────────────────────────

    st.subheader("🛠️ Recommended actions")

    if actions:
        for action in actions:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(
                        f"### {action['action']}"
                    )
                    st.write(action["rationale"])

                with col2:
                    st.metric(
                        "Priority",
                        action["priority"],
                    )

                if action["evidence_ids"]:
                    st.caption(
                        "Evidence: "
                        + ", ".join(action["evidence_ids"])
                    )
    else:
        st.info(
            "No action was recommended. "
            "Human investigation is required."
        )

    # ─────────────────────────────────────────────
    # Human validation
    # ─────────────────────────────────────────────

    validation_status = analysis.get(
        "validation_status",
        "pending",
    )

    st.subheader("👤 Human validation")

    if validation_status == "pending":
        st.write(
            "Review the diagnosis, evidence and recommendation "
            "before taking action."
        )

        validated_by = st.text_input(
            "Operator",
            value="operator-001",
            key="validated_by",
        )

        comment = st.text_area(
            "Validation comment",
            placeholder=(
                "Explain why you approve or reject "
                "the recommendation."
            ),
            key="validation_comment",
        )

        col1, col2 = st.columns(2)

        with col1:
            approve = st.button(
                "✅ Approve recommendation",
                use_container_width=True,
            )

        with col2:
            reject = st.button(
                "❌ Reject recommendation",
                use_container_width=True,
            )

        if approve or reject:
            validation_status_value = (
                "approved" if approve else "rejected"
            )

            request_id = analysis["request_id"]

            with st.spinner("Recording validation..."):
                try:
                    response = requests.post(
                        f"{API_URL}/analyses/"
                        f"{request_id}/validation",
                        json={
                            "status": validation_status_value,
                            "validated_by": validated_by,
                            "comment": comment or None,
                        },
                        timeout=10,
                    )
                except requests.RequestException as exc:
                    st.error(
                        f"Unable to reach OpsPilot API: {exc}"
                    )
                    st.stop()

            if response.status_code != 200:
                st.error(
                    f"Validation failed "
                    f"({response.status_code}): "
                    f"{response.text}"
                )
                st.stop()

            st.session_state["analysis"] = response.json()
            st.rerun()

    elif validation_status == "approved":
        st.success("✅ Recommendation approved.")

        st.write(
            f"Validated by: "
            f"**{analysis.get('validated_by', 'unknown')}**"
        )

        if analysis.get("validation_comment"):
            st.write(
                f"**Comment:** "
                f"{analysis['validation_comment']}"
            )

    elif validation_status == "rejected":
        st.error("❌ Recommendation rejected.")

        st.write(
            f"Validated by: "
            f"**{analysis.get('validated_by', 'unknown')}**"
        )

        if analysis.get("validation_comment"):
            st.write(
                f"**Comment:** "
                f"{analysis['validation_comment']}"
            )
    st.divider()

    if st.button(
        "＋ Launch new analysis",
        key="launch_new_analysis",
        type="primary",
        use_container_width=True,
    ):
        reset_analysis()
        st.rerun()    