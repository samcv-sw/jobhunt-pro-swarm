"""
tests/stress_deliverability_suite.py
High-Load Empirical Stress Benchmark & Edge Case Analyzer for Deliverability Shield.
"""

import os
import re
import sys
import time
import sqlite3
import tempfile
import threading
from datetime import datetime, timedelta, date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.spintax_engine import expand_spintax, calculate_jaccard_distance, generate_unique_variations
from core.email_verifier import (
    verify_email_deliverability,
    is_deliverable_email,
    check_365_cooldown_dedup,
    check_domain_mx,
    get_verifier_stats
)
from core.email_warmup import EmailWarmup, WARMUP_SCHEDULE


def run_benchmark():
    print("=" * 70)
    print("🚀 RUNNING EMPIRICAL ADVERSARIAL STRESS BENCHMARK")
    print("=" * 70)
    results = {}

    # ── 1. Spintax Deep Nesting & High-Iteration Benchmark ──
    print("\n[1] Testing Spintax Engine at Scale...")
    nested_template = "Hello {World|{Earth|{Terra|{Globe|{Sol-3|{Galaxy|Universe}}}}}}, {we {love|enjoy}|I {appreciate|value}} your {innovative|cutting-edge|groundbreaking} work."
    t0 = time.time()
    for i in range(2000):
        out = expand_spintax(nested_template, seed=i)
        assert "{" not in out and "}" not in out
    elapsed_spintax = time.time() - t0
    print(f"  ✓ 2,000 deep nested spintax expansions completed in {elapsed_spintax:.4f}s ({2000/elapsed_spintax:.1f} ops/sec)")
    results["spintax_2k_time_s"] = elapsed_spintax

    # ── 2. Jaccard Distance Token Set Mathematical Verification ──
    print("\n[2] Testing Jaccard Distance Calculation...")
    # Disjoint
    assert calculate_jaccard_distance("a b c", "x y z") == 1.0
    # Exact match
    assert calculate_jaccard_distance("a b c", "A B C.") == 0.0
    # Half overlap: {"a", "b"} vs {"b", "c"} -> union {"a", "b", "c"} (3), inter {"b"} (1) -> sim 1/3 -> dist 2/3 (0.6667)
    d = calculate_jaccard_distance("a b", "b c")
    assert abs(d - (2.0 / 3.0)) < 0.001
    print(f"  ✓ Jaccard distance mathematical correctness verified (Disjoint: 1.0, Identical: 0.0, Partial: {d:.4f})")
    results["jaccard_correctness"] = "PASSED"

    # ── 3. High-Load Cooldown Deduplication Verification ──
    print("\n[3] Testing 365-Day Cooldown Window under Heavy Load...")
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=10000;")
            conn.execute("CREATE TABLE campaigns (campaign_id TEXT PRIMARY KEY, user_id TEXT)")
            conn.execute("CREATE TABLE campaign_emails (id INTEGER PRIMARY KEY, campaign_id TEXT, email_address TEXT, sent_at TIMESTAMP)")
            conn.execute("CREATE TABLE multi_platform_apps (id INTEGER PRIMARY KEY, user_id TEXT, email TEXT, applied_at TIMESTAMP)")
            conn.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY, user_id TEXT, email TEXT, applied_at TIMESTAMP, created_at TIMESTAMP)")

            # Insert 10,000 past records
            now = datetime.now()
            conn.execute("INSERT INTO campaigns VALUES ('c_perf', 'user_heavy')")
            ce_batch = [
                ('c_perf', f"lead_{i}@enterprise.com", (now - timedelta(days=i % 700)).strftime("%Y-%m-%d %H:%M:%S"))
                for i in range(5000)
            ]
            conn.executemany("INSERT INTO campaign_emails (campaign_id, email_address, sent_at) VALUES (?, ?, ?)", ce_batch)
            conn.commit()

        # Check performance of 1,000 cooldown evaluations against 5,000 record DB
        t0 = time.time()
        blocked_count = 0
        allowed_count = 0
        for i in range(1000):
            target = f"lead_{i}@enterprise.com"
            allowed, _ = check_365_cooldown_dedup("user_heavy", target, db_path=temp_db)
            if allowed:
                allowed_count += 1
            else:
                blocked_count += 1
        elapsed_dedup = time.time() - t0
        print(f"  ✓ 1,000 Cooldown checks over 5,000 DB records in {elapsed_dedup:.4f}s ({1000/elapsed_dedup:.1f} lookups/sec)")
        print(f"    Blocked (<=365d): {blocked_count}, Allowed (>365d): {allowed_count}")
        assert blocked_count > 0 and allowed_count > 0
        results["cooldown_1k_time_s"] = elapsed_dedup
    finally:
        import gc
        gc.collect()
        if os.path.exists(temp_db):
            try:
                os.unlink(temp_db)
            except Exception:
                pass

    # ── 4. Warmup Multi-Thread Concurrency Stress Test ──
    print("\n[4] Testing Warmup SQLite Concurrency (50 threads x 10 increments)...")
    fd, temp_db2 = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        warmup = EmailWarmup(db_path=temp_db2)
        test_domain = "fastmail.stress.com"
        warmup.get_status(test_domain)  # initialize

        num_threads = 50
        increments = 10
        errors = []

        def worker():
            try:
                w = EmailWarmup(db_path=temp_db2)
                for _ in range(increments):
                    w.record_send(test_domain, count=1)
                    time.sleep(0.0005)
            except Exception as e:
                errors.append(e)

        t_list = [threading.Thread(target=worker) for _ in range(num_threads)]
        t0 = time.time()
        for t in t_list:
            t.start()
        for t in t_list:
            t.join()
        elapsed_warmup = time.time() - t0

        final_sent = warmup.get_sent_today(test_domain)
        expected_sent = num_threads * increments
        print(f"  ✓ 50 concurrent worker threads completed 500 atomic DB increments in {elapsed_warmup:.4f}s")
        print(f"    Expected Sent: {expected_sent} | Actual Sent in SQLite: {final_sent} | Errors: {len(errors)}")
        assert len(errors) == 0, f"Encountered thread errors: {errors}"
        assert final_sent == expected_sent, f"Race condition detected: {final_sent} != {expected_sent}"
        results["warmup_concurrency"] = "PASSED"
    finally:
        import gc
        gc.collect()
        if os.path.exists(temp_db2):
            try:
                os.unlink(temp_db2)
            except Exception:
                pass

    # ── 5. Synthetic Hex & Malformed Email Deliverability Stress ──
    print("\n[5] Testing Deliverability Filter & Anti-Synthetic Rules...")
    test_cases = [
        ("careers@oracle.com", True),
        ("careers-hub-1234abcd@oracle.com", False),
        ("careers-a1b2c3d4e5f6@company.com", False),
        ("recruitment@microsoft.com", True),
        ("careers@google.com", True),
        ("recruiter@fake.com", False),
        ("user@gmai.com", False),
        ("test@example.com", False),
        ("seniorarchitect1.com", False)
    ]
    for email, expected in test_cases:
        actual = is_deliverable_email(email)
        assert actual == expected, f"Deliverability mismatch for {email}: expected {expected}, got {actual}"
    print(f"  ✓ Anti-Synthetic Hex & Deliverability Filter 100% compliant ({len(test_cases)} assertions)")
    results["deliverability_compliance"] = "PASSED"

    print("\n" + "=" * 70)
    print("🎯 ALL ADVERSARIAL BENCHMARK TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_benchmark()
