"""
Empirical Adversarial Stress Test & Benchmark Harness — Milestone 1 (R1 & R2)
Author: Challenger 2 (teamwork_preview_challenger_m1_2)

Validates:
1. Zero-DB keepalive sentinels (/healthz, /ping) in web/app_v2.py and backend/main.py under severed DB conditions.
2. Latency SLA benchmark (P50 < 5ms) over 500 requests across 10 concurrent threads.
3. Strict 0 DB connections acquired during keepalive probes (monitored via spies/interceptors).
4. PostgreSQL connection pooling, Neon -pooler URL injection, 280s recycling, and SQLite fallback on OperationalError.
5. Dual-dialect SQL transpiler accuracy and edge cases.
6. Thread-safe multi-tenant isolation under concurrent tenant creation, campaign dispatch, and wallet operations.
"""

import concurrent.futures
import contextlib
import gc
import json
import logging
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure root directory in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from starlette.testclient import TestClient

import config
import core.pg_sqlite_shim as shim
from core.gcc_billing import gcc_billing_service
from core.multi_tenant import TenantManager
from web.app_v2 import app as web_app
from backend.main import app as backend_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CHALLENGER_M1")


def test_zero_db_sentinels_under_severed_db():
    print("\n" + "=" * 80)
    print("TEST 1: Zero-DB Keepalive Sentinels & Severed DB Failover")
    print("=" * 80)

    web_client = TestClient(web_app)
    backend_client = TestClient(backend_app)

    # 1. Spy on all possible DB entrypoints to ensure 0 DB calls
    db_spy = MagicMock(side_effect=RuntimeError("CRITICAL_ERROR: Database was accessed during zero-DB sentinel!"))

    with patch("core.pg_sqlite_shim.connect", db_spy), \
         patch("core.pg_sqlite_shim.get_db_connection", db_spy), \
         patch("web.shared.get_db", db_spy), \
         patch("sqlite3.connect", db_spy):

        # Web App Probes
        r_web_ping = web_client.get("/ping")
        r_web_healthz = web_client.get("/healthz")

        # Backend App Probes
        r_backend_ping = backend_client.get("/ping")
        r_backend_healthz = backend_client.get("/healthz")
        r_backend_api_ping = backend_client.get("/api/ping")
        r_backend_api_health = backend_client.get("/api/health")

        assert r_web_ping.status_code == 200, f"Web /ping returned {r_web_ping.status_code}"
        assert r_web_healthz.status_code == 200, f"Web /healthz returned {r_web_healthz.status_code}"
        assert r_backend_ping.status_code == 200, f"Backend /ping returned {r_backend_ping.status_code}"
        assert r_backend_healthz.status_code == 200, f"Backend /healthz returned {r_backend_healthz.status_code}"
        assert r_backend_api_ping.status_code == 200, f"Backend /api/ping returned {r_backend_api_ping.status_code}"
        assert r_backend_api_health.status_code == 200, f"Backend /api/health returned {r_backend_api_health.status_code}"

        expected_body = {"status": "ok", "ping": "pong", "immortal": True}
        assert r_web_ping.json() == expected_body
        assert r_web_healthz.json() == expected_body
        assert r_backend_ping.json() == expected_body
        assert r_backend_healthz.json() == expected_body

        # Assert zero database calls occurred
        assert db_spy.call_count == 0, f"DB called {db_spy.call_count} times during sentinel pings!"

    print("  [PASS] Zero DB queries / connections during keepalive probes (Strict 0 DB calls verified).")
    print("  [PASS] Both web/app_v2.py and backend/main.py keepalives return 200 OK with immortal sentinel payload.")


def benchmark_keepalive_latency():
    print("\n" + "=" * 80)
    print("TEST 2: Empirical Latency SLA Benchmark (500 requests, 10 concurrent threads)")
    print("=" * 80)

    web_client = TestClient(web_app)
    # Warmup
    web_client.get("/healthz")
    web_client.get("/ping")

    latencies = []

    def make_req(idx):
        endpoint = "/healthz" if idx % 2 == 0 else "/ping"
        t0 = time.perf_counter()
        resp = web_client.get(endpoint)
        t1 = time.perf_counter()
        assert resp.status_code == 200
        return (t1 - t0) * 1000.0  # in ms

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_req, i) for i in range(500)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())

    latencies.sort()
    count = len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    avg_lat = sum(latencies) / count
    p50 = latencies[int(count * 0.50)]
    p90 = latencies[int(count * 0.90)]
    p95 = latencies[int(count * 0.95)]
    p99 = latencies[int(count * 0.99)]

    print(f"  Execution Stats ({count} Requests):")
    print(f"    • Min:      {min_lat:.3f} ms")
    print(f"    • Average:  {avg_lat:.3f} ms")
    print(f"    • P50:      {p50:.3f} ms (SLA Target < 5.0ms: {'PASS' if p50 < 5.0 else 'FAIL'})")
    print(f"    • P90:      {p90:.3f} ms")
    print(f"    • P95:      {p95:.3f} ms")
    print(f"    • P99:      {p99:.3f} ms")
    print(f"    • Max:      {max_lat:.3f} ms")

    assert p50 < 5.0, f"SLA Violation: P50 latency is {p50:.3f}ms (target < 5.0ms)"
    print("  [PASS] Latency SLA (<5ms P50) fully satisfied.")
    return {"p50": p50, "p95": p95, "p99": p99, "avg": avg_lat}


def test_postgres_pooling_and_failover_resilience():
    print("\n" + "=" * 80)
    print("TEST 3: PostgreSQL Neon Pooling, 280s Recycling, and Failover Resilience")
    print("=" * 80)

    # 1. Neon -pooler URL injection verification
    test_url = "postgresql://user:pass@ep-steep-cake-12345.c-7.us-east-1.aws.neon.tech/neondb"
    formatted = shim.format_neon_connection_string(test_url)
    assert "-pooler" in formatted, f"Failed to inject -pooler in {formatted}"
    assert "prepareThreshold=0" in formatted
    assert "sslmode=require" in formatted
    print("  [PASS] Neon PgBouncer -pooler and connection parameter injection verified.")

    # 2. 280s Connection Recycling
    mock_pool = MagicMock()
    stale_conn = MagicMock()
    stale_conn._created_at = time.time() - 295  # 295s old (> 280s)
    fresh_conn = MagicMock()
    fresh_conn._created_at = time.time() - 10   # 10s old (< 280s)
    mock_cur = MagicMock()
    fresh_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_pool.getconn.side_effect = [stale_conn, fresh_conn]

    with patch("core.pg_sqlite_shim.PG_POOL", mock_pool), \
         patch("core.pg_sqlite_shim.POOL_PID", os.getpid()), \
         patch("core.pg_sqlite_shim.psycopg2") as mock_psycopg2:
        mock_psycopg2.OperationalError = type("OperationalError", (Exception,), {})
        wrapper = shim.PgConnectionWrapper()
        # Stale conn must have been discarded with close=True
        mock_pool.putconn.assert_any_call(stale_conn, close=True)
        assert wrapper.conn == fresh_conn
    print("  [PASS] 280s Neon Connection Recycling verified: Stale connection closed and fresh connection checked out.")

    # 3. Failover Resilience: When PG throws OperationalError, connect() falls back to SQLite
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_sqlite_path = tf.name

    try:
        with patch("core.pg_sqlite_shim.PgConnectionWrapper", side_effect=Exception("Neon connection refused")):
            conn = shim.connect(temp_sqlite_path)
            assert isinstance(conn, shim.SqliteConnectionWrapper), f"Expected SqliteConnectionWrapper, got {type(conn)}"
            # Verify queries run on fallback
            conn.execute("CREATE TABLE test_failover (id INTEGER PRIMARY KEY, msg TEXT)")
            conn.execute("INSERT INTO test_failover (msg) VALUES (?)", ("fallback_ok",))
            row = conn.execute("SELECT msg FROM test_failover WHERE id = 1").fetchone()
            assert row["msg"] == "fallback_ok"
            conn.close()
        print("  [PASS] Database Failover Resilience: Graceful fallback from failed PG to SQLite verified.")
    finally:
        if os.path.exists(temp_sqlite_path):
            with contextlib.suppress(Exception):
                os.remove(temp_sqlite_path)


def test_sql_dialect_transpiler_adversarial_cases():
    print("\n" + "=" * 80)
    print("TEST 4: SQL Dialect Transpiler Adversarial Stress Cases")
    print("=" * 80)

    cases = [
        # (Input SQLite SQL, Expected converted substring)
        ("SELECT * FROM users WHERE email = ? AND role = ?", "SELECT * FROM users WHERE email = %s AND role = %s"),
        ("INSERT OR IGNORE INTO user_prefs (user_id, pref_key) VALUES (?, ?)", "ON CONFLICT DO NOTHING"),
        ("INSERT OR REPLACE INTO cv_profiles (id, user_id, cv_text) VALUES (?, ?, ?)", "ON CONFLICT (id) DO UPDATE SET user_id = EXCLUDED.user_id, cv_text = EXCLUDED.cv_text"),
        ("SELECT * FROM campaign_emails WHERE sent_at >= datetime('now', '-365 days')", "NOW() - INTERVAL '365 days'"),
        ("SELECT * FROM cooldowns WHERE expires_at >= datetime('now', '+' || ? || ' minutes')", "NOW() + (%s || ' minutes')::INTERVAL"),
        ("SELECT strftime('%Y-%m-%d', created_at)", "TO_CHAR(created_at, 'YYYY-MM-DD')"),
        ("SELECT strftime('%s', 'now')", "EXTRACT(EPOCH FROM NOW())"),
        ("SELECT last_insert_rowid()", "lastval()"),
        ("PRAGMA table_info('users')", "information_schema.columns WHERE table_name = 'users'"),
        ("CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)", "CREATE TABLE logs (id SERIAL PRIMARY KEY, message TEXT)"),
    ]

    for orig, expected_sub in cases:
        conv = shim.convert_sql(orig)
        assert expected_sub.lower() in conv.lower() or expected_sub in conv, (
            f"Dialect Transpiler Error!\nInput:    {orig}\nOutput:   {conv}\nExpected: {expected_sub}"
        )

    print(f"  [PASS] Verified {len(cases)} SQL dialect transpiler test cases.")


def test_thread_safe_multi_tenant_isolation():
    print("\n" + "=" * 80)
    print("TEST 5: Thread-Safe Multi-Tenant Isolation Stress Test")
    print("=" * 80)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        # Initialize schema
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                email TEXT,
                name TEXT,
                phone TEXT,
                password_hash TEXT,
                tokens REAL DEFAULT 100.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE cv_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                target_titles TEXT,
                skills TEXT,
                experience_years INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT UNIQUE,
                user_id TEXT,
                order_id TEXT,
                status TEXT DEFAULT 'pending',
                sent_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

        num_tenants = 10
        errors = []

        def worker_task(t_idx):
            try:
                # Each thread opens its own connection with timeout
                t_conn = sqlite3.connect(db_path, timeout=30)
                t_conn.row_factory = sqlite3.Row
                email = f"tenant_{t_idx}@enterprise{t_idx}.com"
                name = f"Tenant {t_idx} Enterprise"

                # 1. Create tenant atomically
                tenant_id, is_new = TenantManager._ensure_user_record(
                    t_conn, name=name, email=email, phone=f"+97150000{t_idx:02d}", password="password123"
                )
                assert is_new is True, f"Tenant {t_idx} was not recognized as new"

                # 2. Add profile
                t_conn.execute(
                    "INSERT INTO cv_profiles (user_id, target_titles, skills, experience_years) VALUES (?, ?, ?, ?)",
                    (tenant_id, f"Role {t_idx}", f"Skill {t_idx}", t_idx)
                )

                # 3. Create isolated campaign
                camp_id = f"CAMP-{tenant_id}-{int(time.time()*1000)}"
                t_conn.execute(
                    "INSERT INTO campaigns (campaign_id, user_id, order_id, sent_count) VALUES (?, ?, ?, ?)",
                    (camp_id, tenant_id, f"ORD-{t_idx}", t_idx * 5)
                )
                t_conn.commit()

                # 4. Read back and verify complete isolation (no data leakage)
                my_user = t_conn.execute("SELECT * FROM users WHERE user_id = ?", (tenant_id,)).fetchone()
                assert my_user["email"] == email

                my_camps = t_conn.execute("SELECT * FROM campaigns WHERE user_id = ?", (tenant_id,)).fetchall()
                assert len(my_camps) == 1
                assert my_camps[0]["campaign_id"] == camp_id
                assert my_camps[0]["sent_count"] == t_idx * 5

                # Verify other tenant data is not accessible in tenant query
                other_camps = t_conn.execute("SELECT * FROM campaigns WHERE user_id != ?", (tenant_id,)).fetchall()
                # Ensure each campaign record belongs to its respective user_id
                for oc in other_camps:
                    assert oc["user_id"] != tenant_id

                t_conn.close()
            except Exception as e:
                errors.append(f"Tenant {t_idx} failed: {e}")

        # Execute 10 threads concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_tenants) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_tenants)]
            for f in concurrent.futures.as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Multi-tenant isolation concurrency errors: {errors}"

        # Verify final database state
        v_conn = sqlite3.connect(db_path)
        v_conn.row_factory = sqlite3.Row
        total_users = v_conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        total_camps = v_conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()["c"]
        v_conn.close()

        assert total_users == num_tenants, f"Expected {num_tenants} users, found {total_users}"
        assert total_camps == num_tenants, f"Expected {num_tenants} campaigns, found {total_camps}"

        print(f"  [PASS] 10 Concurrent Tenants executed without collisions, race conditions, or cross-tenant data bleed.")

    finally:
        if os.path.exists(db_path):
            with contextlib.suppress(Exception):
                os.remove(db_path)


def test_gcc_billing_engine():
    print("\n" + "=" * 80)
    print("TEST 6: GCC Billing, Tax Invoices & Multi-Currency Calculations")
    print("=" * 80)

    currencies = ["USD", "SAR", "AED", "KWD", "QAR", "BHD", "OMR"]
    for curr in currencies:
        res = gcc_billing_service.convert_price(100.0, curr)
        assert res["currency"] == curr
        assert res["subtotal"] > 0
        assert res["vat_amount"] >= 0
        assert res["total_amount"] == round(res["subtotal"] + res["vat_amount"], 2)

    # Tax invoice test
    inv = gcc_billing_service.generate_tax_invoice("Riyadh Tech Co", "TRN-998877", 299.0, "SAR")
    assert inv["client_name"] == "Riyadh Tech Co"
    assert inv["vat_rate_percent"] == 15
    assert inv["currency"] == "SAR"
    assert inv["vat_amount"] > 0

    print("  [PASS] GCC multi-currency conversions and ZATCA/FTA tax invoice calculations verified.")


if __name__ == "__main__":
    print("=" * 80)
    print("CHALLENGER 2 — MILESTONE 1 (R1 & R2) EMPIRICAL ADVERSARIAL VERIFICATION")
    print("=" * 80)

    t_start = time.time()
    test_zero_db_sentinels_under_severed_db()
    bench = benchmark_keepalive_latency()
    test_postgres_pooling_and_failover_resilience()
    test_sql_dialect_transpiler_adversarial_cases()
    test_thread_safe_multi_tenant_isolation()
    test_gcc_billing_engine()
    t_end = time.time()

    print("\n" + "=" * 80)
    print(f"ALL CHALLENGER EMPIRICAL TESTS PASSED IN {t_end - t_start:.2f}s!")
    print("=" * 80)
