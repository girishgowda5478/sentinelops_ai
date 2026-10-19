import logging
import os

from fastapi import FastAPI
from sentinel.schemas import AnalyzeRequest
from sentinel.analysis import analyze_incident
from sentinel.llm import investigate_with_ai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelops")

app = FastAPI(
    title="SentinelOps AI API",
    version="0.2.1",
    description="Evidence-based incident investigation.",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "sentinelops-ai",
        "ai_configured": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    baseline = analyze_incident(request.summary, request.logs, request.deployment)
    try:
        ai_result = investigate_with_ai(
            summary=request.summary,
            evidence=baseline["evidence"],
            existing_hypotheses=baseline["hypotheses"],
            deployment=request.deployment,
        )
        return {**baseline, **ai_result, "evidence": baseline["evidence"]}
    except Exception as exc:
        # Log only exception type/message locally; never log environment variables or API keys.
        logger.warning("Groq investigation failed (%s): %s", type(exc).__name__, _safe_error(exc))
        return {
            **baseline,
            "metadata": {
                "analysis_mode": "deterministic_fallback",
                "remediation_executed": False,
                "ai_error_type": type(exc).__name__,
            },
            "ai_warning": "AI investigation was unavailable. Check the FastAPI terminal for the sanitized diagnostic message.",
        }


def _safe_error(exc: Exception) -> str:
    # Avoid echoing credential-like values if a provider error happens to include them.
    message = str(exc)[:400]
    key = os.getenv("GROQ_API_KEY", "")
    if key:
        message = message.replace(key, "[REDACTED]")
    return message
