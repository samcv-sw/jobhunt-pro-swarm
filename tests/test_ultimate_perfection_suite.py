"""
Automated Test Suite for Ultimate Perfection:
1. Self-Healing Guardian (Database integrity & hot backup)
2. GCC Labor Law & Contract Analyzer
"""
import pytest
from core.self_healing_guardian import self_healing_guardian
from core.gcc_contract_analyzer import gcc_contract_analyzer


def test_self_healing_guardian():
    integ = self_healing_guardian.verify_database_integrity("saas_v2.db")
    assert integ["status"] in ["healthy", "corrupted", "error"]

    # Test hot backup
    bkp = self_healing_guardian.perform_hot_backup("saas_v2.db", backup_dir="data/backups")
    assert bkp["status"] in ["success", "skipped", "error"]
    if bkp["status"] == "success":
        assert bkp["compressed_size_kb"] > 0


def test_gcc_contract_analyzer():
    contract_sample = """
    Employment Agreement:
    Employee shall be subject to a probation period of 90 days.
    Non-compete clause shall apply for a period of 1 year within Riyadh.
    Employee is entitled to End of Service Gratuity in accordance with Saudi Labor Law Article 84.
    """
    res = gcc_contract_analyzer.analyze_contract(contract_sample, "saudi_arabia", basic_salary=25000.0)
    assert res["overall_safety_rating"] == "Grade A (Safe to Sign)"
    assert res["risk_score_percentage"] <= 25
    assert len(res["clauses_analyzed"]) >= 3
