"""JobHunt Pro — Zero-Trust Supply Chain & Dependency Audit Engine.

Scans dependencies across requirements files, detects suspicious packages,
enforces version pinning, and validates supply-chain safety (IMP-ZeroTrust).
"""

import os
import sys
import re
from typing import List, Dict, Tuple, Any

KNOWN_MALICIOUS_PATTERNS = [
    r"^eval-",
    r"-stealer$",
    r"^pypi-test-pkg",
    r"discord-token",
    r"request-logger-malicious"
]

def audit_requirements_file(filepath: str) -> Dict[str, Any]:
    """
    Audits a python requirements file for pinning, formatting, and safety.
    """
    if not os.path.exists(filepath):
        return {"status": "skipped", "reason": "file_not_found", "file": filepath}

    issues: List[str] = []
    total_packages = 0
    pinned_packages = 0

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        total_packages += 1

        # Check for version pinning (== or >=)
        if "==" in line or ">=" in line or "~=" in line:
            pinned_packages += 1
        else:
            issues.append(f"Line {line_num}: Unpinned package '{line}'. Explicit version pinning recommended.")

        # Check for suspicious patterns
        pkg_name = line.split("==")[0].split(">=")[0].split("~=")[0].strip()
        for pat in KNOWN_MALICIOUS_PATTERNS:
            if re.search(pat, pkg_name, re.IGNORECASE):
                issues.append(f"CRITICAL: Suspicious package pattern detected '{pkg_name}' on line {line_num}!")

    pin_ratio = round((pinned_packages / total_packages) * 100, 1) if total_packages > 0 else 100.0

    return {
        "status": "passed" if len(issues) == 0 else "warning",
        "file": filepath,
        "total_packages": total_packages,
        "pinned_packages": pinned_packages,
        "pinning_percentage": pin_ratio,
        "issues": issues
    }

def run_full_supply_chain_audit(project_dir: str) -> Dict[str, Any]:
    """
    Runs full zero-trust audit across all requirement manifests in project.
    """
    manifests = ["requirements.txt", "requirements-cloud.txt", "requirements-dev.txt"]
    results = {}
    total_issues = 0

    for m in manifests:
        full_path = os.path.join(project_dir, m)
        audit_res = audit_requirements_file(full_path)
        results[m] = audit_res
        total_issues += len(audit_res.get("issues", []))

    return {
        "status": "secure" if total_issues == 0 else "audit_warnings",
        "total_issues_found": total_issues,
        "manifest_reports": results
    }

if __name__ == "__main__":
    pwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report = run_full_supply_chain_audit(pwd)
    print("=== ZERO TRUST SUPPLY CHAIN AUDIT REPORT ===")
    print(f"Status: {report['status']}")
    print(f"Total Issues: {report['total_issues_found']}")
    for k, v in report["manifest_reports"].items():
        print(f"[{k}] Pinning: {v.get('pinning_percentage', 0)}% ({v.get('pinned_packages', 0)}/{v.get('total_packages', 0)})")
        for iss in v.get("issues", []):
            print(f"  - {iss}")
