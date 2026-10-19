from sentinel.analysis import extract_evidence, analyze_incident

def test_extracts_error_events_and_services():
    logs = """2026-10-19T10:00:00Z INFO service=api event=ok
2026-10-19T10:01:00Z ERROR service=api event=db_timeout message="database connection timed out"
"""
    result = extract_evidence(logs)
    assert result["event_count"] == 2
    assert result["error_count"] == 1
    assert "api" in result["services"]
    assert result["event_counts"]["db_timeout"] == 1

def test_database_timeout_creates_hypothesis():
    result = analyze_incident(
        "checkout is failing",
        '2026-10-19T10:01:00Z ERROR service=checkout event=db_timeout message="database connection timed out"',
        ""
    )
    assert result["hypotheses"][0]["cause"] == "Database connectivity or saturation"
    assert result["metadata"]["remediation_executed"] is False

def test_empty_logs_have_no_crash():
    result = analyze_incident("unknown issue", "", "")
    assert result["evidence"]["event_count"] == 0
    assert result["hypotheses"]
