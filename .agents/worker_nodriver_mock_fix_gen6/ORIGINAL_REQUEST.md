## 2026-07-06T08:21:31Z
You are a worker agent assigned to fix a test mock in the project.

Your objective:
1. Locate `tests/test_stealth_parser_and_fallbacks.py`.
2. Modify the `nodriver` mock inside `test_nodriver_fallback_passes_proxy` and `test_nodriver_fallback_resolves_default_proxy_when_none` so that instead of using the module-level `@patch("nodriver.start", ...)` decorator (which causes `ModuleNotFoundError` if `nodriver` is not installed during test loading/discovery), you dynamically mock `sys.modules["nodriver"]` inside the test body.
For example, instead of:
```python
@pytest.mark.asyncio
@patch("nodriver.start", new_callable=AsyncMock)
async def test_nodriver_fallback_passes_proxy(mock_uc_start):
```
use:
```python
@pytest.mark.asyncio
async def test_nodriver_fallback_passes_proxy():
    import sys
    mock_uc_start = AsyncMock()
    mock_nodriver = MagicMock()
    mock_nodriver.start = mock_uc_start
    with patch.dict(sys.modules, {"nodriver": mock_nodriver}):
```
Make sure you mock both `test_nodriver_fallback_passes_proxy` and `test_nodriver_fallback_resolves_default_proxy_when_none` correctly.
3. Run the full test suite using `pytest` to confirm all 253 tests pass cleanly.
4. Record your changes, the pytest commands used, and the full pytest output in your handoff report.
5. Create your agent metadata folder `.agents/worker_nodriver_mock_fix_gen6` and write your `progress.md` and `handoff.md` there.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
