from collections import Counter
import re
from datetime import datetime

ERROR_WORDS = ("error", "exception", "failed", "timeout", "critical", "fatal", "http_500", "http 500")

def extract_evidence(logs: str) -> dict:
    lines = [line.strip() for line in logs.splitlines() if line.strip()]
    errors = [line for line in lines if any(word in line.lower() for word in ERROR_WORDS)]
    services = sorted(set(re.findall(r"\bservice=([A-Za-z0-9_.-]+)", logs)))
    events = Counter(re.findall(r"\bevent=([A-Za-z0-9_.-]+)", logs))
    timestamps = re.findall(r"\b\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\dZ?\b", logs)
    return {
        "event_count": len(lines),
        "error_count": len(errors),
        "error_rate": round(len(errors) / len(lines), 3) if lines else 0,
        "services": services,
        "event_counts": dict(events),
        "error_samples": errors[:8],
        "timestamps_observed": timestamps[:10],
    }

def deterministic_hypotheses(evidence: dict, deployment: str) -> list[dict]:
    events = evidence["event_counts"]
    hypotheses = []
    if events.get("db_timeout", 0) or any(any(term in x.lower() for term in ("database connection timed out", "database connection timeout", "db timeout", "db_timeout")) for x in evidence["error_samples"]):
        hypotheses.append({
            "rank": 1,
            "cause": "Database connectivity or saturation",
            "confidence": "Medium",
            "reasoning": "Repeated database timeout evidence is consistent with connection exhaustion, database overload, or a network/connectivity issue. Logs alone do not distinguish these causes.",
            "evidence": evidence["error_samples"][:4],
            "checks": [
                "Inspect database connection-pool utilization and wait time.",
                "Check database CPU, active connections, and query latency for the incident window.",
                "Verify network errors and database health from the affected service."
            ]
        })
    if events.get("http_500", 0) or any("http 500" in x.lower() or "http_500" in x.lower() for x in evidence["error_samples"]):
        hypotheses.append({
            "rank": len(hypotheses) + 1,
            "cause": "Upstream failures propagating as HTTP 500 responses",
            "confidence": "Medium",
            "reasoning": "HTTP 500 events occurring alongside dependency errors may indicate that failed dependency calls are propagating to API requests.",
            "evidence": [x for x in evidence["error_samples"] if "http_500" in x.lower() or "http 500" in x.lower() or "request failed" in x.lower()][:4],
            "checks": [
                "Correlate request IDs between API errors and dependency failures.",
                "Review exception handling and timeout behavior in the request path."
            ]
        })
    if deployment:
        hypotheses.append({
            "rank": len(hypotheses) + 1,
            "cause": "Recent deployment as a possible contributing factor",
            "confidence": "Low",
            "reasoning": "A deployment was reported, but temporal correlation and a causal link have not been verified.",
            "evidence": [f"User-provided deployment context: {deployment}"],
            "checks": [
                "Compare error rates immediately before and after the deployment.",
                "Review code/configuration changes related to database access and timeout settings.",
                "Compare with a known healthy release before considering rollback."
            ]
        })
    if not hypotheses:
        hypotheses.append({
            "rank": 1,
            "cause": "Insufficient evidence to identify a likely root cause",
            "confidence": "Low",
            "reasoning": "The supplied logs do not contain a recognizable failure signature.",
            "evidence": ["No recognized error signature was detected by the initial rules."],
            "checks": [
                "Provide logs covering the incident start and recovery.",
                "Include request IDs, service names, and dependency errors.",
                "Add metrics for latency, traffic, saturation, and error rate."
            ]
        })
    return hypotheses

def analyze_incident(summary: str, logs: str, deployment: str = "") -> dict:
    evidence = extract_evidence(logs)
    hypotheses = deterministic_hypotheses(evidence, deployment)
    plan = [
        "Confirm the incident window and affected user-facing service.",
        "Validate the highest-ranked hypothesis against independent metrics and logs.",
        "Check dependency health and recent changes before selecting a mitigation.",
        "Apply any remediation only through the team's approved change process.",
        "Verify recovery using error rate, latency, and service-health indicators."
    ]
    return {
        "overview": f"Investigated: {summary}. Parsed {evidence['event_count']} log lines and found {evidence['error_count']} error-like events. Hypotheses are evidence-based starting points, not confirmed root causes.",
        "evidence": evidence,
        "hypotheses": hypotheses,
        "response_plan": plan,
        "metadata": {"analysis_mode": "deterministic_mvp", "remediation_executed": False}
    }
