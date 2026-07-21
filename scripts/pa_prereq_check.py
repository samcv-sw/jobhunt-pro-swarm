#!/usr/bin/env python3
"""
JobHunt Pro — Deployment Prerequisite Validator (Credential-Free)
==================================================================

Validates that the local repository is fully wired for PythonAnywhere
deployment via the GitHub Actions `deploy-pythonanywhere` job + the `/deploy`
webhook. It NEVER requires live PA credentials — it only checks that the
files, endpoint, workflow, env-var docs, and dependency are present.

Run:  python scripts/pa_prereq_check.py
Exit: 0 = all prerequisites satisfied, 1 = something missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> repo root


def _check(label: str, ok: bool, detail: str = "") -> bool:
    status = "OK  " if ok else "FAIL"
    line = f"[{status}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def main() -> int:
    all_ok = True

    # 1. Core app file + required symbols
    app_file = ROOT / "web" / "app_v2.py"
    ok = app_file.is_file()
    all_ok &= _check("web/app_v2.py exists", ok)
    if ok:
        text = app_file.read_text(encoding="utf-8", errors="ignore")
        all_ok &= _check('/deploy endpoint present',
                         '@app.post("/deploy")' in text)
        all_ok &= _check("wsgi_app export present", "wsgi_app" in text)
        all_ok &= _check("DEPLOY_SECRET read in /deploy",
                         "DEPLOY_SECRET" in text and "DEPLOY_ALLOWED_IPS" in text)

    # 2. WSGI bridge artifact
    wsgi_bridge = ROOT / "scripts" / "pa_wsgi_bridge.py"
    all_ok &= _check("scripts/pa_wsgi_bridge.py exists", wsgi_bridge.is_file())

    # 3. deploy.yml workflow wiring
    wf = ROOT / ".github" / "workflows" / "deploy.yml"
    if wf.is_file():
        wf_text = wf.read_text(encoding="utf-8", errors="ignore")
        all_ok &= _check("deploy.yml has deploy-pythonanywhere job",
                         "deploy-pythonanywhere" in wf_text)
        all_ok &= _check("deploy.yml references PYTHONANYWHERE_DEPLOY_HOOK_URL",
                         "PYTHONANYWHERE_DEPLOY_HOOK_URL" in wf_text)
        all_ok &= _check("deploy.yml references PYTHONANYWHERE_DEPLOY_SECRET",
                         "PYTHONANYWHERE_DEPLOY_SECRET" in wf_text)
    else:
        all_ok &= _check("deploy.yml exists", False)

    # 4. .env.example documents deploy vars
    env_ex = ROOT / ".env.example"
    if env_ex.is_file():
        env_text = env_ex.read_text(encoding="utf-8", errors="ignore")
        for var in ("DEPLOY_SECRET", "DEPLOY_ALLOWED_IPS",
                    "PYTHONANYWHERE_DEPLOY_HOOK_URL", "PYTHONANYWHERE_DEPLOY_SECRET"):
            all_ok &= _check(f".env.example has {var}", var in env_text)
    else:
        all_ok &= _check(".env.example exists", False)

    # 5. a2wsgi dependency declared
    declared = False
    for req in (ROOT / "requirements.txt", ROOT / "pyproject.toml"):
        if req.is_file() and "a2wsgi" in req.read_text(encoding="utf-8", errors="ignore"):
            _check(f"a2wsgi declared in {req.name}", True)
            declared = True
            break
    if not declared:
        all_ok &= _check("a2wsgi declared in requirements", False)

    print()
    if all_ok:
        print("[DONE] All deployment prerequisites satisfied. Ready for PythonAnywhere deploy.")
        return 0
    print("[FAIL] Some prerequisites are missing. Fix the FAIL items above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
