# Handoff Report: E2E Testing Analysis for R3 and R5

## 1. Observation
I directly observed and analyzed the following components in the project workspace:

### A. Scraper Stealth Logic (`scrapers/stealth_ingest.py`)
- **Proxy rotation**: The scraper loads proxies from the environment:
  ```python
  12: PROXY_LIST = os.getenv("RESIDENTIAL_PROXIES", "").split(",")
  ```
  And selects them randomly:
  ```python
  16: def get_random_proxy() -> dict:
  17:     if not PROXY_LIST or not PROXY_LIST[0]:
  18:         return {}
  19:     proxy = random.choice(PROXY_LIST)
  20:     return {"http": proxy, "https": proxy}
  ```
- **TLS Spoofing**: Implemented via `curl_cffi` using impersonate profiles:
  ```python
  13: STEALTH_PROFILES = ["chrome110", "chrome116", "chrome120", "safari15_3", "safari15_5"]
  ...
  76:     impersonate_profile = random.choice(STEALTH_PROFILES)
  77: 
  78:     async with requests.AsyncSession(
  79:         impersonate=impersonate_profile,
  80:         proxies=proxy_config,
  81:         headers=headers,
  82:     ) as session:
  ```
- **Warmup step & session isolation**: The scraper performs a two-stage fetch with session isolation:
  ```python
  87:             # 1. Organic warmup — hit root domain first to collect clearance cookies
  88:             await session.get(root_domain, timeout=15)
  89:             await asyncio.sleep(random.uniform(2.0, 5.0))
  90: 
  91:             # 2. Fetch the actual target
  92:             response = await session.get(url, timeout=15)
  ```
- **Fallback Headers**: If `proxy_config` is empty, it generates a spoofed `x-forwarded-for` header:
  ```python
  68:     if not proxy_config:
  69:         headers = {
  70:             "x-forwarded-for": (
  71:                 f"{random.randint(1,255)}.{random.randint(1,255)}"
  72:                 f".{random.randint(1,255)}.{random.randint(1,255)}"
  73:             )
  74:         }
  ```

### B. CI/CD Production Workflow (`.github/workflows/production.yml`)
- **Backend Tests Configuration**:
  ```yaml
  20:     - name: Install dependencies
  21:       run: |
  22:         python -m pip install --upgrade pip
  23:         pip install -r requirements.txt
  24:         pip install pytest httpx
  25:         
  26:     - name: Test with pytest
  27:       run: |
  28:         python -m pytest tests/test_backend.py -v
  ```
- **Observed Execution Behavior**:
  - Running `python -m pytest tests/test_backend.py -v` locally blocks/hangs because `test_scrape_endpoint_queues_task` attempts to invoke Celery `scrape_jobs.delay` without mock wrappers. This blocks indefinitely while attempting to connect to a non-existent local Redis instance (`redis://localhost:6379/0`).
  - Running `python -m pytest tests/e2e/test_backend.py -v` succeeds (6 passed in 4.12s) because it mocks out Celery dispatches via monkeypatch.
  - Running `python -m pytest tests/e2e/test_database.py -v` (4 passed) and `tests/e2e/test_frontend.py -v` (7 passed) succeeds.
  - Running `python -m pytest tests/test_anti_ban.py -v` (12 passed) succeeds.

---

## 2. Logic Chain
My step-by-step reasoning is structured as follows:

1. **Scraper Stealth logic is highly reliant on external configuration and libraries**:
   - `curl_cffi` requires native C-bindings (`libcurl-impersonate`) to successfully spoof TLS fingerprints. If these libraries fail to compile/load or are not installed in the running environment, execution crashes.
   - The fallback mechanism (`x-forwarded-for`) is easily stripped by CDNs, meaning testing must ensure it is not relied upon in production without proper warnings.
   - There are no existing tests for `stealth_ingest.py`. Therefore, E2E tests must be introduced to verify its operation.

2. **The current CI/CD workflow contains critical gaps**:
   - The production workflow file only runs a single test file: `tests/test_backend.py`.
   - The other unit tests (`tests/test_anti_ban.py`) and all files under `tests/e2e/` (`test_backend.py`, `test_database.py`, `test_frontend.py`) are skipped in the CI pipeline.
   - The `requirements.txt` file does not contain necessary packages for the stealth scraper (such as `curl_cffi` or `beautifulsoup4`). Consequently, if the workflow attempts to execute all tests, it will crash with `ModuleNotFoundError` unless dependencies are consolidated.
   - Running the default `tests/test_backend.py` inside a stateless GitHub Action runner will hang or fail unless a Redis broker container is configured, or tasks are mocked out like in the E2E suite.

---

## 3. Caveats
- Since this is a read-only investigation, I have not implemented any code changes or fixed the `.github/workflows/production.yml` workflow.
- I assumed the existence of a mock server or local server wrapper inside the E2E suite to run network-less tests. In CODE_ONLY network mode, actual external websites cannot be pinged to verify TLS bypassing.

---

## 4. Conclusion
1. **R3 (Scraper Stealth Hardening)**: The scraper logic is sound but untested. We must introduce E2E tests that verify proxy rotation, organic warmup sequencing, fallback headers, and TLS impersonation using localized HTTP mocking or unit-level monkeypatching of the `requests.AsyncSession` constructor.
2. **R5 (CI/CD Pipeline Verification)**: The current production CI/CD workflow is deficient. It only runs `tests/test_backend.py` (which is prone to blocking without a running Redis instance) and fails to run the rest of the test suite. We need to write an E2E meta-test to verify the workflow configuration and expand the CI/CD pipeline steps to install all dependencies and run all test targets.

---

## 5. Verification Method

### A. E2E Test Strategy for R3 (Scraper Stealth)
To verify proxy rotation and TLS spoofing, we recommend creating a test file `tests/e2e/test_stealth_scraper.py`:

```python
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from scrapers.stealth_ingest import process_single_job, get_random_proxy

@pytest.mark.asyncio
async def test_proxy_rotation_logic(monkeypatch):
    # Mock proxy list
    monkeypatch.setenv("RESIDENTIAL_PROXIES", "http://proxy1:8080,http://proxy2:8080")
    
    # Reload proxy list
    import scrapers.stealth_ingest
    scrapers.stealth_ingest.PROXY_LIST = ["http://proxy1:8080", "http://proxy2:8080"]
    
    proxies = [get_random_proxy() for _ in range(10)]
    assert all("http" in p for p in proxies)
    # Ensure at least some rotation occurs
    assert len(set(p["http"] for p in proxies)) > 1

@pytest.mark.asyncio
async def test_stealth_warmup_and_tls_profile_call():
    # Mock requests.AsyncSession to trace calls
    mock_session = AsyncMock()
    mock_session.get = AsyncMock()
    
    with patch("curl_cffi.requests.AsyncSession", return_value=mock_session):
        # We also mock asyncio.sleep to keep tests fast
        with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
            url = "https://example.com/job/1"
            await process_single_job(url)
            
            # Assert 2 GET calls: first root domain, then the actual target URL
            assert mock_session.get.call_count == 2
            
            first_call_args = mock_session.get.call_args_list[0][0][0]
            second_call_args = mock_session.get.call_args_list[1][0][0]
            
            assert first_call_args == "https://example.com/"
            assert second_call_args == url
            mock_sleep.assert_called_once()
```

### B. E2E Test Strategy for R5 (CI/CD Production Workflow)
To verify the CI/CD pipeline structure without pushing to GitHub, write a yaml validator E2E test `tests/e2e/test_cicd_config.py`:

```python
import os
import yaml

def test_production_workflow_validity():
    workflow_path = ".github/workflows/production.yml"
    assert os.path.exists(workflow_path), f"CI/CD workflow not found at {workflow_path}"
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    assert config is not None
    assert "jobs" in config
    assert "backend-tests" in config["jobs"]
    assert "frontend-build" in config["jobs"]
    
    # Assert that Node 20 and Python 3.12 are explicitly used
    backend_steps = config["jobs"]["backend-tests"]["steps"]
    setup_python = next(s for s in backend_steps if "setup-python" in s.get("uses", ""))
    assert setup_python["with"]["python-version"] == "3.12"
    
    frontend_steps = config["jobs"]["frontend-build"]["steps"]
    setup_node = next(s for s in frontend_steps if "setup-node" in s.get("uses", ""))
    assert setup_node["with"]["node-version"] == "20"
```

### C. Execution and Verification Commands
To execute the tests locally and check they pass:
```powershell
# Run the entire E2E test suite
python -m pytest tests/e2e/ -v

# Run the anti-ban unit tests
python -m pytest tests/test_anti_ban.py -v
```
