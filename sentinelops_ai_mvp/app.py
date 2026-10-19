import json
import os
import streamlit as st
import requests

st.set_page_config(page_title="SentinelOps AI", page_icon="🚨", layout="wide")
st.title("🚨 SentinelOps AI")
st.caption("Evidence-backed incident investigation and root-cause hypotheses")

API_URL = st.sidebar.text_input("API URL", value=os.getenv("SENTINELOPS_API_URL", "http://127.0.0.1:8000"))
st.sidebar.info("MVP uses synthetic incident logs. Recommendations are advisory; no remediation actions are executed.")

SAMPLE_LOGS = """2026-10-19T10:00:00Z INFO service=checkout event=request_ok latency_ms=120
2026-10-19T10:01:00Z INFO service=checkout event=request_ok latency_ms=135
2026-10-19T10:02:00Z ERROR service=checkout event=db_timeout latency_ms=5000 message="database connection timed out"
2026-10-19T10:02:10Z ERROR service=checkout event=db_timeout latency_ms=5000 message="database connection timed out"
2026-10-19T10:02:20Z ERROR service=checkout event=http_500 latency_ms=5200 message="request failed after database timeout"
2026-10-19T10:03:00Z WARN service=checkout event=latency_high latency_ms=4800
2026-10-19T10:04:00Z ERROR service=checkout event=db_timeout latency_ms=5000 message="database connection timed out"
"""
logs = st.text_area("Paste incident logs", value=SAMPLE_LOGS, height=260)
col1, col2 = st.columns([1, 1])
with col1:
    incident = st.text_input("Incident summary", "Checkout API has elevated latency and HTTP 500 errors")
with col2:
    deployment = st.text_input("Recent deployment (optional)", "checkout-service v2.4 deployed at 09:58 UTC")

if st.button("Investigate incident", type="primary", use_container_width=True):
    if not logs.strip():
        st.warning("Paste some logs first.")
    else:
        try:
            with st.spinner("Analyzing evidence..."):
                response = requests.post(
                    f"{API_URL.rstrip('/')}/analyze",
                    json={"summary": incident, "logs": logs, "deployment": deployment},
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()
            st.subheader("Incident overview")
            a, b, c = st.columns(3)
            a.metric("Events parsed", result["evidence"]["event_count"])
            b.metric("Error events", result["evidence"]["error_count"])
            c.metric("Services observed", len(result["evidence"]["services"]))
            st.write(result["overview"])
            st.subheader("Evidence")
            st.json(result["evidence"])
            st.subheader("Root-cause hypotheses")
            for item in result["hypotheses"]:
                with st.expander(f'{item["rank"]}. {item["cause"]} — {item["confidence"]} confidence', expanded=True):
                    st.write(item["reasoning"])
                    st.markdown("**Supporting evidence**")
                    for evidence in item["evidence"]:
                        st.markdown(f"- {evidence}")
                    st.markdown("**Next diagnostic checks**")
                    for check in item["checks"]:
                        st.markdown(f"- {check}")
            st.subheader("Recommended response plan")
            for i, step in enumerate(result["response_plan"], 1):
                st.markdown(f"{i}. {step}")
            st.warning("AI hypotheses are not proof. Verify evidence before making operational changes.")
            st.download_button("Download incident report (JSON)", json.dumps(result, indent=2), "sentinelops_incident_report.json", "application/json")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the API at {API_URL}. Start the FastAPI server and retry. Details: {exc}")
        except Exception as exc:
            st.error(f"Analysis failed: {type(exc).__name__}: {exc}")

st.divider()
st.caption("SentinelOps AI MVP • Read-only analysis • No automatic remediation.")
