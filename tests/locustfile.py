import os
import time

import jwt
from locust import HttpUser, between, task


def _build_load_test_token() -> str | None:
    token = os.getenv("LOCUST_BEARER_TOKEN")
    if token:
        return token

    secret = os.getenv("LOCUST_JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    if not secret:
        return None

    now = int(time.time())
    payload = {
        "sub": os.getenv("LOCUST_USER_ID", "locust_user"),
        "role": os.getenv("LOCUST_USER_ROLE", "jobseeker"),
        "iat": now,
        "exp": now + int(os.getenv("LOCUST_JWT_TTL_SECONDS", "3600")),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class JobHuntProUser(HttpUser):
    """
    IMP-099: Locust load testing configuration.
    Simulates concurrent users loading dashboard metrics, submitting CVs, and calling system endpoints.
    """
    # Wait between 2 and 4 seconds between tasks to avoid unrealistic rate spikes.
    wait_time = between(2, 4)

    def on_start(self):
        self.auth_headers = None
        token = _build_load_test_token()
        if token:
            self.auth_headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def view_system_status(self):
        """Simulate users loading the cloud status endpoint."""
        self.client.get("/api/v2/cloud-tick/status")

    @task(1)
    def mock_onboarding_test_run(self):
        """Simulate users triggering onboarding checks."""
        if not self.auth_headers:
            return
        self.client.post("/api/v1/onboarding/test-run", headers=self.auth_headers)

    @task(2)
    def view_landing_page(self):
        """Simulate users browsing pages."""
        self.client.get("/en/pricing")
        self.client.get("/en/faq")
