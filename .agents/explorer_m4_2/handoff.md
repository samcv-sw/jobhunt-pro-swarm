# Cloudflare Health-Check-Based DNS Failover Solution (IMP-128) Design Report

## 1. Observation

During analysis of the codebase, the following files and lines were observed:
- **Health Check Endpoints (`backend/main.py`)**:
  - Line 450: A lightweight health endpoint `/health` returning basic status:
    ```python
    @app.get("/health")
    async def health_check(request: Request = None) -> dict[str, str]:
        return {"status": "ok", "architecture": "FastAPI + Celery + Redis"}
    ```
  - Line 457: An ultra-lightweight endpoint `/healthz` returning simple status:
    ```python
    @app.get("/healthz")
    async def healthz(request: Request = None) -> dict[str, str]:
        return {"status": "ok"}
    ```
  - Line 487: A deep detailed health endpoint `/api/v1/health/detailed` probing database, Redis, SMTP, and Groq API:
    ```python
    @app.get("/api/v1/health/detailed")
    @cache(expire=15)
    async def health_detailed(request: Request = None) -> dict[str, Any]:
        # ... checks DB, Redis sync ping, SMTP open_connection, and Groq API http check ...
    ```
- **Existing Health Tests (`tests/test_health_monitor.py`)**:
  - Lines 34-165 contain unit tests mock-probing components in `health_detailed`. These tests serve as a template for structuring mock-based assertions using `unittest.mock.patch` and `unittest.mock.AsyncMock`.
- **Infrastructure Context**:
  - `cloudflare/wrangler.toml` and `cloudflare/DEPLOY_GUIDE.md` indicate static frontend resources are served on Cloudflare Pages (`https://jobhunt-pro.pages.dev`).
  - `infrastructure/deploy_eu_cloud.sh` defines Hetzner/Scaleway deployment routes, indicating multi-region scaling needs.

---

## 2. Logic Chain

To implement multi-region DNS failover (`IMP-128`), we must map Cloudflare's Load Balancing constructs onto our infrastructure:
1. **Load Balancer Monitor**: Configures how Cloudflare polls our origin.
   - **Crucial Architecture Decision**: Cloudflare Load Balancing typically checks health from multiple edge regions at high frequency (e.g., every 60 seconds). Pointing Cloudflare's Monitor to the deep `/api/v1/health/detailed` endpoint would cause excessive load on dependencies (specifically Neon DB connection limits and Upstash Redis rate limits, which are tightly capped at 10 concurrent connections as per `IMP-126`).
   - **Recommendation**: Route the Cloudflare Monitor to `/healthz` or `/health` (lightweight endpoints that do not hit downstream databases or third-party APIs). Keep `/api/v1/health/detailed` strictly for local self-healing/telemetry.
2. **Load Balancer Pools**: Group origin servers by geographical region (e.g., Primary Pool: PythonAnywhere/Render US; Fallback Pool: Hetzner/Scaleway EU).
3. **Load Balancer**: Binds a DNS hostname (e.g., `api.jobhuntpro.com`) to the pools with an active routing policy (e.g., `off` for primary/secondary failover, `geo` for proximity-based routing).

The automation script must handle idempotent synchronization (Check-Before-Create) via the Cloudflare API v4. Since API calls can fail due to authentication issues, rate limits, or account subscription constraints (Load Balancing is a paid add-on on Cloudflare Free/Pro plans), we must implement robust wrapper error parsing to yield clear output messages.

---

## 3. Caveats

- **Billing Restrictions**: Cloudflare Load Balancing is a paid feature. Attempting to create monitors, pools, or load balancers via the API on an account without a subscription will throw Cloudflare error code `1002` or similar billing validation errors. The script must intercept and explain this error clearly.
- **Local Sandbox Limits**: In CODE_ONLY network mode, we cannot test the script live against actual Cloudflare endpoints. Therefore, a comprehensive mock test suite is required to guarantee functionality.
- **API Token Scopes**: The Cloudflare API Token needs standard `Account.Load Balancers and Monitors: Edit` and `Zone.Load Balancers: Edit` permissions.

---

## 4. Conclusion

We propose the following implementation design for the automation script and its unit tests:

### A. Automation Script Design (`scripts/cloudflare_failover_setup.py`)
```python
"""
scripts/cloudflare_failover_setup.py

Automates provisioning of Cloudflare Load Balancer Monitors, Pools, and Load Balancers.
Idempotently updates existing resources instead of duplicating them.
"""

import os
import sys
import logging
from typing import Any, Dict, List, Optional
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cloudflare_failover")

class CloudflareAPIError(Exception):
    """Custom exception representing Cloudflare API failures."""
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []

class CloudflareFailoverManager:
    def __init__(self, api_token: str, account_id: str, zone_id: str):
        self.account_id = account_id
        self.zone_id = zone_id
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.cloudflare.com/client/v4"

    def _request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Performs HTTP request to Cloudflare API with strict error verification."""
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.request(method, url, headers=self.headers, json=json_data)
                
                # Check for HTTP level errors
                response.raise_for_status()
                data = response.json()
                
                # Check Cloudflare response envelope
                if not data.get("success", False):
                    errors = data.get("errors", [])
                    err_msg = ", ".join([f"{e.get('message')} (code: {e.get('code')})" for e in errors])
                    raise CloudflareAPIError(f"Cloudflare API Error: {err_msg}", errors=errors)
                
                return data
        except httpx.HTTPStatusError as exc:
            # Handle standard error formats returned by CF with HTTP non-2xx status
            try:
                err_data = exc.response.json()
                errors = err_data.get("errors", [])
                err_msg = ", ".join([f"{e.get('message')} (code: {e.get('code')})" for e in errors])
                raise CloudflareAPIError(f"HTTP {exc.response.status_code}: {err_msg}", errors=errors)
            except Exception:
                raise CloudflareAPIError(f"HTTP status error: {exc}")
        except httpx.RequestError as exc:
            raise CloudflareAPIError(f"Network error communicating with Cloudflare: {exc}")

    # --- MONITOR OPERATIONS (Account Level) ---

    def list_monitors(self) -> List[Dict[str, Any]]:
        path = f"/accounts/{self.account_id}/load_balancers/monitors"
        return self._request("GET", path).get("result", [])

    def create_monitor(self, monitor_data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/accounts/{self.account_id}/load_balancers/monitors"
        return self._request("POST", path, json_data=monitor_data).get("result", {})

    def update_monitor(self, monitor_id: str, monitor_data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/accounts/{self.account_id}/load_balancers/monitors/{monitor_id}"
        return self._request("PUT", path, json_data=monitor_data).get("result", {})

    def sync_monitor(self, monitor_data: Dict[str, Any]) -> str:
        """Idempotently syncs a monitor, matching on path and description."""
        monitors = self.list_monitors()
        target_path = monitor_data.get("path")
        target_desc = monitor_data.get("description")
        
        existing_monitor = None
        for m in monitors:
            if m.get("path") == target_path and m.get("description") == target_desc:
                existing_monitor = m
                break
                
        if existing_monitor:
            m_id = existing_monitor["id"]
            logger.info(f"Monitor already exists. Updating monitor {m_id}...")
            self.update_monitor(m_id, monitor_data)
            return m_id
        else:
            logger.info("Creating new health check monitor...")
            new_monitor = self.create_monitor(monitor_data)
            return new_monitor["id"]

    # --- POOL OPERATIONS (Account Level) ---

    def list_pools(self) -> List[Dict[str, Any]]:
        path = f"/accounts/{self.account_id}/load_balancers/pools"
        return self._request("GET", path).get("result", [])

    def create_pool(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/accounts/{self.account_id}/load_balancers/pools"
        return self._request("POST", path, json_data=pool_data).get("result", {})

    def update_pool(self, pool_id: str, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/accounts/{self.account_id}/load_balancers/pools/{pool_id}"
        return self._request("PUT", path, json_data=pool_data).get("result", {})

    def sync_pool(self, pool_data: Dict[str, Any]) -> str:
        """Idempotently syncs a pool, matching on name."""
        pools = self.list_pools()
        target_name = pool_data.get("name")
        
        existing_pool = None
        for p in pools:
            if p.get("name") == target_name:
                existing_pool = p
                break
                
        if existing_pool:
            p_id = existing_pool["id"]
            logger.info(f"Pool '{target_name}' already exists. Updating pool {p_id}...")
            self.update_pool(p_id, pool_data)
            return p_id
        else:
            logger.info(f"Creating new pool '{target_name}'...")
            new_pool = self.create_pool(pool_data)
            return new_pool["id"]

    # --- LOAD BALANCER OPERATIONS (Zone Level) ---

    def list_load_balancers(self) -> List[Dict[str, Any]]:
        path = f"/zones/{self.zone_id}/load_balancers"
        return self._request("GET", path).get("result", [])

    def create_load_balancer(self, lb_data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/zones/{self.zone_id}/load_balancers"
        return self._request("POST", path, json_data=lb_data).get("result", {})

    def update_load_balancer(self, lb_id: str, lb_data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/zones/{self.zone_id}/load_balancers/{lb_id}"
        return self._request("PUT", path, json_data=lb_data).get("result", {})

    def sync_load_balancer(self, lb_data: Dict[str, Any]) -> str:
        """Idempotently syncs a load balancer, matching on name."""
        lbs = self.list_load_balancers()
        target_name = lb_data.get("name")
        
        existing_lb = None
        for lb in lbs:
            if lb.get("name") == target_name:
                existing_lb = lb
                break
                
        if existing_lb:
            lb_id = existing_lb["id"]
            logger.info(f"Load balancer for '{target_name}' already exists. Updating LB {lb_id}...")
            self.update_load_balancer(lb_id, lb_data)
            return lb_id
        else:
            logger.info(f"Creating new load balancer for '{target_name}'...")
            new_lb = self.create_load_balancer(lb_data)
            return new_lb["id"]

def run_sync(config: Dict[str, Any]) -> Dict[str, str]:
    """Runs the synchronization workflow."""
    api_token = config["api_token"]
    account_id = config["account_id"]
    zone_id = config["zone_id"]
    
    manager = CloudflareFailoverManager(api_token, account_id, zone_id)
    
    # 1. Sync Monitor
    monitor_payload = config["monitor"]
    monitor_id = manager.sync_monitor(monitor_payload)
    
    # 2. Sync Pools (attaching the monitor ID)
    pool_ids = []
    for pool in config["pools"]:
        pool["monitor"] = monitor_id
        p_id = manager.sync_pool(pool)
        pool_ids.append(p_id)
        
    # 3. Sync Load Balancer (linking the synced pools)
    lb_payload = config["load_balancer"]
    lb_payload["default_pools"] = pool_ids
    lb_payload["fallback_pool"] = pool_ids[0]  # First pool acts as fallback
    lb_id = manager.sync_load_balancer(lb_payload)
    
    return {
        "monitor_id": monitor_id,
        "pool_ids": ",".join(pool_ids),
        "load_balancer_id": lb_id
    }

if __name__ == "__main__":
    # Example Config Loader
    import json
    
    token = os.getenv("CLOUDFLARE_API_TOKEN")
    acc_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    z_id = os.getenv("CLOUDFLARE_ZONE_ID")
    
    if not all([token, acc_id, z_id]):
        logger.error("Missing required environment variables: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_ZONE_ID")
        sys.exit(1)
        
    app_config = {
        "api_token": token,
        "account_id": acc_id,
        "zone_id": z_id,
        "monitor": {
            "type": "http",
            "description": "JobHunt Pro API Health Check",
            "path": "/healthz",
            "method": "GET",
            "port": 443,
            "timeout": 5,
            "retries": 2,
            "interval": 60,
            "expected_codes": "200",
            "follow_redirects": False,
            "allow_insecure": False
        },
        "pools": [
            {
                "name": "jobhunt-pro-us-pool",
                "description": "Primary US Region Pool",
                "origins": [
                    {
                        "name": "render-us",
                        "address": "jobhunt-pro-us.onrender.com",
                        "enabled": True,
                        "weight": 1
                    }
                ],
                "enabled": True,
                "minimum_origins": 1
            },
            {
                "name": "jobhunt-pro-eu-pool",
                "description": "Secondary EU Region Pool",
                "origins": [
                    {
                        "name": "hetzner-eu",
                        "address": "jobhunt-pro-eu.hydra-node.de",
                        "enabled": True,
                        "weight": 1
                    }
                ],
                "enabled": True,
                "minimum_origins": 1
            }
        ],
        "load_balancer": {
            "name": "api.jobhuntpro.com",
            "description": "JobHunt Pro API Load Balancer Failover",
            "proxied": True,
            "steering_policy": "off", # strictly failover logic
            "enabled": True
        }
    }
    
    try:
        results = run_sync(app_config)
        logger.info(f"Failover infrastructure synchronized successfully: {results}")
    except CloudflareAPIError as e:
        logger.error(f"Failed to configure Cloudflare failover: {e}")
        # Detect lack of subscription / billing restrictions
        if any(err.get("code") in (1002, 1001) for err in e.errors):
            logger.error("👉 Please ensure that you have purchased a Cloudflare Load Balancing subscription in your dashboard.")
        sys.exit(2)
```

---

### B. Unit Test Design (`tests/test_cloudflare_failover_setup.py`)
```python
"""
tests/test_cloudflare_failover_setup.py

Mock-based unit tests for the Cloudflare DNS failover synchronization script.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx
from scripts.cloudflare_failover_setup import (
    CloudflareFailoverManager,
    CloudflareAPIError,
    run_sync
)

# Shared Mock Config Data
MOCK_CONFIG = {
    "api_token": "mock_token",
    "account_id": "acc_123",
    "zone_id": "zone_456",
    "monitor": {"path": "/healthz", "description": "JobHunt Pro API Health Check"},
    "pools": [
        {"name": "jobhunt-pro-us-pool", "origins": []},
        {"name": "jobhunt-pro-eu-pool", "origins": []}
    ],
    "load_balancer": {"name": "api.jobhuntpro.com"}
}

def test_sync_creates_resources_when_missing():
    """Verify that if resources do not exist, POST requests are called to create them."""
    
    # 1. Mock lists returning empty lists
    # 2. Mock creations returning success IDs
    mock_responses = [
        # List Monitors GET
        MagicMock(status_code=200, json=lambda: {"success": True, "result": []}),
        # Create Monitor POST
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "mon_new_id"}}),
        # List Pools GET
        MagicMock(status_code=200, json=lambda: {"success": True, "result": []}),
        # Create Pool 1 POST
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "pool_us_id"}}),
        # List Pools GET (called for secondary pool check)
        MagicMock(status_code=200, json=lambda: {"success": True, "result": []}),
        # Create Pool 2 POST
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "pool_eu_id"}}),
        # List Load Balancers GET
        MagicMock(status_code=200, json=lambda: {"success": True, "result": []}),
        # Create Load Balancer POST
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "lb_new_id"}}),
    ]

    with patch("httpx.Client.request", side_effect=mock_responses) as mock_request:
        result = run_sync(MOCK_CONFIG)
        
        assert result["monitor_id"] == "mon_new_id"
        assert result["pool_ids"] == "pool_us_id,pool_eu_id"
        assert result["load_balancer_id"] == "lb_new_id"
        
        # Verify call patterns
        post_methods = [call[0][0] for call in mock_request.call_args_list if call[0][0] == "POST"]
        assert len(post_methods) == 4  # 1 Monitor + 2 Pools + 1 Load Balancer

def test_sync_updates_resources_when_existing():
    """Verify that if resources already exist, PUT requests are called to update them."""
    
    existing_monitors = [{"id": "mon_old_id", "path": "/healthz", "description": "JobHunt Pro API Health Check"}]
    existing_pools = [
        {"id": "pool_us_old_id", "name": "jobhunt-pro-us-pool"},
        {"id": "pool_eu_old_id", "name": "jobhunt-pro-eu-pool"}
    ]
    existing_lbs = [{"id": "lb_old_id", "name": "api.jobhuntpro.com"}]

    mock_responses = [
        # List Monitors GET
        MagicMock(status_code=200, json=lambda: {"success": True, "result": existing_monitors}),
        # Update Monitor PUT
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "mon_old_id"}}),
        # List Pools GET (US check)
        MagicMock(status_code=200, json=lambda: {"success": True, "result": existing_pools}),
        # Update Pool US PUT
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "pool_us_old_id"}}),
        # List Pools GET (EU check)
        MagicMock(status_code=200, json=lambda: {"success": True, "result": existing_pools}),
        # Update Pool EU PUT
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "pool_eu_old_id"}}),
        # List Load Balancers GET
        MagicMock(status_code=200, json=lambda: {"success": True, "result": existing_lbs}),
        # Update Load Balancer PUT
        MagicMock(status_code=200, json=lambda: {"success": True, "result": {"id": "lb_old_id"}}),
    ]

    with patch("httpx.Client.request", side_effect=mock_responses) as mock_request:
        result = run_sync(MOCK_CONFIG)
        
        assert result["monitor_id"] == "mon_old_id"
        assert result["pool_ids"] == "pool_us_old_id,pool_eu_old_id"
        assert result["load_balancer_id"] == "lb_old_id"
        
        # Verify call patterns
        put_calls = [call[0][0] for call in mock_request.call_args_list if call[0][0] == "PUT"]
        assert len(put_calls) == 4  # 1 Monitor + 2 Pools + 1 Load Balancer updated

def test_cloudflare_api_failure_raises_exception():
    """Verify that Cloudflare success: False response envelopes raise CloudflareAPIError."""
    
    mock_error_resp = MagicMock(
        status_code=400,
        json=lambda: {
            "success": False,
            "errors": [{"code": 1002, "message": "Load balancing subscription is required"}],
            "result": None
        }
    )
    
    # Let list_monitors throw a Cloudflare error directly
    with patch("httpx.Client.request", return_value=mock_error_resp):
        with pytest.raises(CloudflareAPIError) as exc_info:
            run_sync(MOCK_CONFIG)
            
        assert "Load balancing subscription is required" in str(exc_info.value)
        assert exc_info.value.errors[0]["code"] == 1002

def test_network_timeout_handles_gracefully():
    """Verify that network issues throw CloudflareAPIError."""
    
    with patch("httpx.Client.request", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(CloudflareAPIError) as exc_info:
            run_sync(MOCK_CONFIG)
            
        assert "Network error" in str(exc_info.value)
```

---

## 5. Verification Method

To verify the correct execution of the design and future implementation:
1. **Validation of Mock Unit Tests**:
   Create a test environment and run `pytest`:
   ```bash
   pytest tests/test_cloudflare_failover_setup.py
   ```
   Check that all 4 test cases pass (handling creates, updates, API-level errors, and timeouts).
2. **Dry Run Integration check**:
   Run the sync script manually with a mock Cloudflare API Token:
   ```bash
   CLOUDFLARE_API_TOKEN=mock_token CLOUDFLARE_ACCOUNT_ID=acc_123 CLOUDFLARE_ZONE_ID=zone_456 python scripts/cloudflare_failover_setup.py
   ```
   Verify that it captures the `CloudflareAPIError` gracefully and outputs the relevant logging error description (in this case, HTTP 401 Unauthorized or API validation failure).
