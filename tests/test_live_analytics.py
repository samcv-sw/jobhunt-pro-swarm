import pytest
from fastapi.testclient import TestClient
from web.app_v2 import app

client = TestClient(app)

def test_sdr_analytics_summary_endpoint():
    """Verify that /api/v2/sdr/analytics-summary returns 200 OK and valid 100% metrics structure."""
    response = client.get("/api/v2/sdr/analytics-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "metrics" in data
    assert data["metrics"]["deliverability_rate"] == "100.0%"
    assert data["metrics"]["mx_shield_active"] is True
    assert data["metrics"]["cooldown_window"] == "365 Days"
    assert data["metrics"]["system_score"] == "100%"

def test_live_analytics_stream_endpoint():
    """Verify that /api/v2/live-analytics-stream returns 200 OK with event-stream content-type."""
    # Use ?limit=1 so the infinite stream terminates (TestClient buffers the full response).
    with client.stream("GET", "/api/v2/live-analytics-stream?limit=1") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        # Read the first event chunk
        for chunk in response.iter_text():
            if chunk:
                assert "deliverability_shield" in chunk
                break
