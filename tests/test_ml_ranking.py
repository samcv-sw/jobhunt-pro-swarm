"""
tests/test_ml_ranking.py — Regression tests for the unified ML job-candidate
ranking engine (core/ml_ranking.py).

Validates big-platform (LinkedIn/Indeed) automation parity:
  * Stable dict shape (no key drift across refactors)
  * Score strictly bounded in [0, 100]
  * Graceful TF-IDF-only fallback when GEMINI_API_KEY is absent
  * Banned-title penalty applies (anti-spam / wrong-role guard)
  * Lexical skill overlap detection
  * Omni-Healing invariant: engine NEVER raises
"""
import sys
from pathlib import Path

import pytest

# Ensure project root is importable (mirrors conftest bootstrap).
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ml_ranking import ml_ranking_engine


STRONG_CV = """
Senior Network Engineer with 8 years of experience in Cisco, MikroTik,
Ubiquiti, Fortinet, Juniper, TCP/IP, VPN, firewalls, routing,
switching, OSPF, BGP, MPLS, VLAN, WAN, LAN, DHCP, DNS,
network security, Wireshark, network monitoring, PRTG, Nagios,
Zabbix, SolarWinds, IT infrastructure, data center, AWS, Azure,
GCP, VMware, Hyper-V, Linux, Windows Server, Active Directory,
PowerShell, Python, Bash, automation, Ansible, Terraform.
"""

STRONG_JOB_TITLE = "Senior Network Engineer"
STRONG_JOB_DESC = """
We are looking for a Senior Network Engineer with strong Cisco, Juniper,
Fortinet, BGP, OSPF, MPLS, VPN, firewall and routing skills.
Experience with AWS, Linux and network automation is a plus.
"""

BANNED_JOB_TITLE = "HR Manager"
BANNED_JOB_DESC = """
Human resources manager needed for recruitment and talent acquisition.
"""


EXPECTED_KEYS = {
    "match_score",
    "skill_match_pct",
    "keyword_matches",
    "missing_keywords",
    "skills_gaps",
    "recommendation",
    "is_fallback",
    "cosine_score",
    "embedding_score",
    "model_used",
}


def test_score_job_match_returns_stable_shape():
    """No key drift — API layer depends on this exact contract."""
    result = ml_ranking_engine.score_job_match(
        cv_text=STRONG_CV,
        job_title=STRONG_JOB_TITLE,
        job_description=STRONG_JOB_DESC,
        user_skills=["cisco", "bgp", "python"],
    )
    missing = EXPECTED_KEYS - set(result.keys())
    assert not missing, f"Missing dict keys: {missing}"


def test_match_score_bounded():
    """Score must stay within [0, 100] for any input."""
    cases = [
        (STRONG_CV, STRONG_JOB_TITLE, STRONG_JOB_DESC),
        ("", "X", "Y"),
        ("random text", "zzz", "qqq"),
    ]
    for cv, title, desc in cases:
        result = ml_ranking_engine.score_job_match(
            cv_text=cv, job_title=title, job_description=desc
        )
        assert isinstance(result["match_score"], int)
        assert 0 <= result["match_score"] <= 100


def test_strong_match_scores_high():
    """A genuinely matching CV must clear the high-priority threshold."""
    result = ml_ranking_engine.score_job_match(
        cv_text=STRONG_CV,
        job_title=STRONG_JOB_TITLE,
        job_description=STRONG_JOB_DESC,
        user_skills=["cisco", "bgp", "python", "aws", "linux"],
    )
    assert result["match_score"] >= 60
    assert result["skill_match_pct"] >= 50
    assert len(result["keyword_matches"]) > 0


def test_banned_title_penalty():
    """Banned titles (HR/recruitment) must suppress the score."""
    clean = ml_ranking_engine.score_job_match(
        cv_text=STRONG_CV,
        job_title=STRONG_JOB_TITLE,
        job_description=STRONG_JOB_DESC,
    )
    banned = ml_ranking_engine.score_job_match(
        cv_text=STRONG_CV,
        job_title=BANNED_JOB_TITLE,
        job_description=BANNED_JOB_DESC,
    )
    assert banned["match_score"] <= clean["match_score"]
    assert banned["match_score"] <= 40


def test_fallback_when_no_gemini_key(monkeypatch):
    """When GEMINI_API_KEY is absent, engine degrades to TF-IDF only."""
    monkeypatch.setattr("core.ml_ranking.config.GEMINI_API_KEY", "")
    result = ml_ranking_engine.score_job_match(
        cv_text=STRONG_CV,
        job_title=STRONG_JOB_TITLE,
        job_description=STRONG_JOB_DESC,
    )
    assert result["model_used"] == "tfidf"
    assert result["embedding_score"] is None
    assert result["is_fallback"] is True


def test_engine_never_raises():
    """Omni-Healing invariant: the engine must never raise."""
    weird_inputs = [
        ("", "", ""),
        (None, None, None),
        ("🚀💻🔥", "🤖", "🛰️"),
        ("a" * 5000, "b" * 5000, "c" * 5000),
    ]
    for cv, title, desc in weird_inputs:
        try:
            res = ml_ranking_engine.score_job_match(
                cv_text=cv or "",
                job_title=title or "",
                job_description=desc or "",
            )
            assert "match_score" in res
        except Exception as e:  # pragma: no cover
            pytest.fail(f"Engine raised on weird input: {e}")
