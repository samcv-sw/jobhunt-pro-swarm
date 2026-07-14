from locust import HttpUser, task, between


class JobHuntProUser(HttpUser):
    """
    IMP-099: Locust load testing configuration.
    Simulates concurrent users loading dashboard metrics, submitting CVs, and calling system endpoints.
    """
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    @task(3)
    def view_system_status(self):
        """Simulate users loading the cloud status endpoint."""
        self.client.get("/api/v2/cloud-tick/status")

    @task(1)
    def mock_onboarding_test_run(self):
        """Simulate users triggering onboarding checks."""
        headers = {"Authorization": "Bearer mock_token_payload"}
        self.client.post("/api/v1/onboarding/test-run", headers=headers)

    @task(2)
    def view_landing_page(self):
        """Simulate users browsing pages."""
        self.client.get("/en/pricing")
        self.client.get("/en/faq")
