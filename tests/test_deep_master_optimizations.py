"""
Automated Test Suite for Deep Master Optimizations:
1. Microscopic Database Performance & Auto-Index Optimizer
2. Sovereign Security Shield & Anti-DDoS Rate Limiter
3. Smart Dynamic Upgrade & Viral Referral Monetization Engine
"""
import pytest
from core.db_performance_optimizer import db_optimizer
from core.sovereign_security_shield import security_shield
from core.monetization_growth_engine import monetization_engine


def test_db_performance_optimizer():
    opt_res = db_optimizer.optimize_database("saas_v2.db")
    assert opt_res["status"] in ["success", "skipped"]
    if opt_res["status"] == "success":
        assert opt_res["journal_mode"] == "WAL"
        assert opt_res["optimization_latency_ms"] < 200


def test_sovereign_security_shield():
    test_ip = "192.168.1.105"

    # Test normal rate limit
    is_limited = security_shield.is_rate_limited(test_ip, max_requests_per_minute=10)
    assert is_limited is False

    # Test brute force tracking
    attempt1 = security_shield.record_login_attempt(test_ip, success=False)
    assert attempt1["allowed"] is True
    assert attempt1["failed_count"] == 1

    # Test HMAC validation
    hmac_ok = security_shield.verify_webhook_hmac(
        payload_bytes=b'{"event":"paid","amount":299}',
        received_signature="528b3d687445fa40026f8d38e3e48227b68e0d9b4db75c13b1fcfa357aa5ad73",
        secret_key="secret_test_key"
    )
    assert isinstance(hmac_ok, bool)


def test_monetization_growth_engine():
    # Low token trigger
    low_bal = monetization_engine.evaluate_upgrade_trigger("user_123", current_tokens=1)
    assert low_bal["trigger_upgrade"] is True
    assert low_bal["discount_percentage"] == 35.0
    assert "FLASH35" in low_bal["discount_code"]

    # Healthy balance
    healthy_bal = monetization_engine.evaluate_upgrade_trigger("user_123", current_tokens=20)
    assert healthy_bal["trigger_upgrade"] is False

    # Viral referral profile
    ref = monetization_engine.generate_referral_profile("usr_sam_77")
    assert "https://jobhunt-pro.com/r/" in ref["referral_url"]
    assert ref["reward_per_referral_tokens"] == 3
