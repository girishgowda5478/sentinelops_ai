# SentinelOps AI

A read-only incident-investigation MVP that extracts evidence from application logs, proposes ranked root-cause hypotheses, and produces diagnostic next steps.

## Architecture

Streamlit UI → FastAPI `/analyze` → deterministic evidence baseline → optional Groq LLM investigation → incident report JSON. If Groq is unavailable, the API returns a rule-based fallback and logs a diagnostic in the FastAPI terminal.

## Run locally (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GROQ_API_KEY = Read-Host "Paste your Groq API key"
uvicorn main:app --reload
```

Open a second terminal in the same folder, activate the environment there too, then run:

```powershell
streamlit run app.py
```

API docs: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health

## Tests

```powershell
pytest -q
```

## Current limitations

- The LLM layer uses Groq when `GROQ_API_KEY` is configured in the same PowerShell session that starts FastAPI; otherwise, it safely falls back to deterministic rules.
- It does not connect to real observability systems or execute remediation.
- Hypotheses are not confirmed root causes.
- Production use would require authentication, rate limits, structured logging, redaction, retention controls, stronger parsing, and evaluation against labeled incidents.

## Roadmap

1. Add a Groq-backed explanation layer using only extracted evidence.
2. Create a labeled synthetic incident benchmark and report top-k diagnosis accuracy.
3. Add structured metrics, incident timelines, and deployment correlation.
4. Add request IDs, log redaction, auth, rate limiting, and observability.
5. Deploy API and UI separately with secrets managed in host settings.
