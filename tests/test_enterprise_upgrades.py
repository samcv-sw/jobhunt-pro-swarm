"""Unit and integration tests for JobHunt Pro enterprise upgrades.

Verifies:
1. Real-time SSE streaming endpoint.
2. CSV lead export & HTML/PDF analytics report export endpoints.
3. Static PWA assets (manifest.json, sw.js).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_export_leads_csv():
    """Verify CSV export endpoint returns 200 OK with text/csv content type."""
    response = client.get("/api/v1/export/leads/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    assert "jobhunt_pro_leads_export.csv" in response.headers["Content-Disposition"]
    
    content = response.text
    assert "Lead ID,Company Name,Contact Person" in content
    assert "Aramco Digital" in content
    assert "NEOM Tech & Digital" in content


def test_export_analytics_pdf():
    """Verify analytics PDF/HTML report endpoint returns 200 OK with HTML content."""
    response = client.get("/api/v1/export/analytics/pdf")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    content = response.text
    assert "JobHunt Pro — Executive B2B Lead Conversion Report" in content
    assert "Total Leads Reached" in content
    assert "LinkedIn B2B SDR Swarm" in content


def test_pwa_static_manifest():
    """Verify manifest.json is served with 200 OK."""
    response = client.get("/static/manifest.json")
    assert response.status_code == 200
    data = response.json()
    assert "JobHunt Pro" in data["short_name"]
    assert data["display"] == "standalone"


def test_pwa_static_service_worker():
    """Verify sw.js service worker script is served with 200 OK."""
    response = client.get("/static/sw.js")
    assert response.status_code == 200
    assert "CACHE_NAME" in response.text
    assert "self.addEventListener" in response.text


def test_sse_live_feed_headers():
    """Verify SSE streaming endpoint headers."""
    # Use ?limit=1 so the infinite stream terminates (TestClient buffers the full response).
    with client.stream("GET", "/api/v1/sse/live-feed?limit=1") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "no-cache" in response.headers["cache-control"]
        body = "".join(response.iter_text())
        assert "event: connect" in body
        assert "event: heartbeat" in body

