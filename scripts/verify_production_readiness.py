"""
verify_production_readiness.py - Comprehensive Production Audit & Health Matrix
Validates environment, database integrity, multi-model AI pool, MX resolver, and payment gateways.
"""

import sys
import os
import json
import logging
import asyncio

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ProductionReadiness")

async def test_database():
    logger.info("--> [1/5] Checking Database Integrity & Connection...")
    from web.shared import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        res = cur.fetchone()
        logger.info(f"    Database Query Execution: PASSED (Returned: {res[0] if res else 'OK'})")
        
        tables_to_check = ["users", "pricing_tiers", "campaign_emails", "processed_webhooks", "redeem_codes"]
        existing = set()
        try:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            existing = {r[0] for r in cur.fetchall()}
        except Exception:
            try:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing = {r[0] for r in cur.fetchall()}
            except Exception:
                pass

        if existing:
            present = [t for t in tables_to_check if t in existing]
            logger.info(f"    Verified schema tables present ({len(present)}/{len(tables_to_check)}): {present}")
        else:
            logger.info("    Database connection active & query execution verified.")
            
        return True
    finally:
        conn.close()

async def test_ai_provider_pool():
    logger.info("--> [2/5] Checking Multi-Model AI Provider Pool...")
    try:
        from core.llm_provider_pool import get_llm_pool
        pool = get_llm_pool()
        active_providers = [name.value for name, is_healthy in pool._health.items() if is_healthy]
        logger.info(f"    Active & Healthy LLM Providers: {len(active_providers)} ({', '.join(active_providers)})")
        return len(active_providers) > 0
    except Exception as e:
        logger.error(f"    AI Pool Error: {e}")
        return False

async def test_mx_deliverability_shield():
    logger.info("--> [3/5] Checking Live MX Deliverability Resolver...")
    try:
        from core.email_verifier import is_deliverable_email
        test_valid = "contact@google.com"
        test_invalid = "invalid_user_never_exist@nonexistent-fake-domain-12345.xyz"
        
        valid_res = is_deliverable_email(test_valid)
        invalid_res = is_deliverable_email(test_invalid)
        
        logger.info(f"    Valid test ({test_valid}): {'PASSED' if valid_res else 'FAILED'}")
        logger.info(f"    Invalid test ({test_invalid}): {'BLOCKED (Expected)' if not invalid_res else 'UNEXPECTED PASS'}")
        return valid_res and not invalid_res
    except Exception as e:
        logger.error(f"    MX Resolver Error: {e}")
        return False

async def test_pricing_and_weapons_catalog():
    logger.info("--> [4/5] Checking Pricing Tiers & Micro-SaaS Catalog...")
    try:
        from core.pricing_manager import PRICING_TIERS, BOUQUET_PACKAGES, SERVICE_PACKAGES
        logger.info(f"    Configured Subscription Tiers: {len(PRICING_TIERS)}")
        logger.info(f"    Configured Bouquet Packages: {len(BOUQUET_PACKAGES)}")
        logger.info(f"    Configured Microservices: {len(SERVICE_PACKAGES)}")
        return len(PRICING_TIERS) >= 4 and len(BOUQUET_PACKAGES) >= 4
    except Exception as e:
        logger.error(f"    Pricing Catalog Error: {e}")
        return False

async def test_payment_endpoints():
    logger.info("--> [5/5] Checking Payment Endpoints & Webhook Security...")
    try:
        from web.routers.payments import router as payments_router
        routes = [route.path for route in payments_router.routes]
        webhook_routes = [r for r in routes if "webhook" in r.lower()]
        logger.info(f"    Total Payment Routes: {len(routes)}")
        logger.info(f"    Active Webhook Endpoints: {len(webhook_routes)}")
        for wr in webhook_routes:
            logger.info(f"      - {wr}")
        return len(webhook_routes) >= 3
    except Exception as e:
        logger.error(f"    Payment Endpoints Error: {e}")
        return False

async def main():
    print("=" * 70)
    print("      JOBHUNT PRO SAAS — ENTERPRISE PRODUCTION READINESS AUDIT")
    print("=" * 70)
    
    results = {
        "Database & Shim Resilience": await test_database(),
        "Multi-Model AI Pool": await test_ai_provider_pool(),
        "Live MX Resolver Shield": await test_mx_deliverability_shield(),
        "Monetization & Catalog": await test_pricing_and_weapons_catalog(),
        "Payment & Webhook Rails": await test_payment_endpoints(),
    }
    
    print("\n" + "=" * 70)
    print("                  AUDIT SCORECARD & SUMMARY")
    print("=" * 70)
    passed = 0
    for name, status in results.items():
        state = "PASSED (10/10)" if status else "FAILED (Needs Attention)"
        print(f"  * {name:<35} : {state}")
        if status:
            passed += 1
            
    score_pct = (passed / len(results)) * 100
    print(f"\nFinal Readiness Score: {score_pct:.1f}% ({passed}/{len(results)} Pillars Verified)")
    print("=" * 70)
    
    if score_pct == 100.0:
        logger.info("ALL SYSTEMS ENTERPRISE PRODUCTION READY (10/10).")
        return 0
    else:
        logger.warning("One or more checks did not pass 100%.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
