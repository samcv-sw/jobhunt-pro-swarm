## 2026-07-11T09:12:58Z
You are teamwork_preview_worker.
Your identity: Worker 1
Your working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_m1_1
Your mission is to implement Milestone 1: Multi-Key JWT Secret Rotation.

Refer to:
- SCOPE.md: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_jwt_rotation\SCOPE.md
- ORIGINAL_REQUEST.md: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_jwt_rotation\ORIGINAL_REQUEST.md
- Synthesis Report: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_jwt_rotation\synthesis.md

Task requirements:
1. Modify `backend/auth.py` to support `JWT_SECRET_KEYS` as a comma-separated list of keys, falling back to `JWT_SECRET_KEY` if missing (and subsequently to the test fallback key). The first key must be exposed as `JWT_SECRET_KEY` (primary key for signing).
2. Implement a helper `decode_jwt_token(token: str) -> dict` in `backend/auth.py` that loops through `JWT_SECRET_KEYS` trying to decode. If signature is valid but expired, raise ExpiredSignatureError immediately.
3. Update `verify_jwt` in `backend/auth.py` to use `decode_jwt_token`.
4. Update WebSocket auth in `backend/main.py` to use `decode_jwt_token`.
5. Sync configuration parsing, `verify_jwt`, and manual decoding in `web/app_v2.py` to align with the multi-key secret logic.
6. Create `tests/test_jwt_rotation.py` containing at least 2 unit tests (and ideally the 4 detailed in `synthesis.md`) verifying config parsing, fallback verification, invalid key rejection, and expired token handling.
7. Run the test suite via pytest (e.g. `python -m pytest tests/ -v` or `pytest`) to verify all 431+ tests (including the new ones) pass with zero regressions.
8. Document all your changes and verification/test results in `handoff.md` in your working directory.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.

Once the changes are completed and verified by tests, send a message back to the orchestrator (conversation ID: 6ecf45d6-6d9d-4904-a199-48bb6826dede) notifying that you are done. Include the absolute path of your handoff.md in the message.
