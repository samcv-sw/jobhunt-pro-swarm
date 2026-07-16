import sqlite3
import time

def benchmark():
    conn = sqlite3.connect("jobhunt_saas_v2.db")
    user_id = "test_user_benchmark"
    
    # Ensure tables exist
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id VARCHAR(64) UNIQUE, wallet_balance DECIMAL(10,2))")
    conn.execute("CREATE TABLE IF NOT EXISTS campaigns (user_id VARCHAR(64), sent_count INT, status VARCHAR(50))")
    
    # Clean and insert dummy data
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM campaigns WHERE user_id = ?", (user_id,))
    conn.execute("INSERT INTO users (user_id, wallet_balance) VALUES (?, 150.50)", (user_id,))
    for i in range(100):
        conn.execute("INSERT INTO campaigns (user_id, sent_count, status) VALUES (?, ?, ?)", (user_id, i, "running" if i % 2 == 0 else "completed"))
    conn.commit()

    # Simulated network latency (10ms round-trip)
    LATENCY = 0.010

    # 1. Benchmark Old Queries
    start_old = time.perf_counter()
    for _ in range(100):
        # First query
        row_camp = conn.execute(
            "SELECT "
            "COALESCE(SUM(sent_count), 0), "
            "COALESCE(SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) "
            "FROM campaigns WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        time.sleep(LATENCY) # simulated network latency

        # Second query
        row4 = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        time.sleep(LATENCY) # simulated network latency

    end_old = time.perf_counter()
    old_time = end_old - start_old

    # 2. Benchmark New Coalesced Query
    start_new = time.perf_counter()
    for _ in range(100):
        # Coalesced query
        row = conn.execute(
            "SELECT "
            "COALESCE(SUM(c.sent_count), 0) AS total_sent, "
            "COALESCE(SUM(CASE WHEN c.status = 'running' THEN 1 ELSE 0 END), 0) AS active_campaigns, "
            "COALESCE(SUM(CASE WHEN c.status = 'completed' THEN 1 ELSE 0 END), 0) AS completed_campaigns, "
            "COALESCE(u.wallet_balance, 0.0) AS wallet_balance "
            "FROM users u "
            "LEFT JOIN campaigns c ON c.user_id = u.user_id "
            "WHERE u.user_id = ? "
            "GROUP BY u.user_id, u.wallet_balance",
            (user_id,)
        ).fetchone()
        time.sleep(LATENCY) # simulated network latency

    end_new = time.perf_counter()
    new_time = end_new - start_new

    improvement = (old_time - new_time) / old_time * 100
    print(f"Old queries time (simulated network): {old_time:.4f}s")
    print(f"New query time (simulated network): {new_time:.4f}s")
    print(f"Speed Improvement: {improvement:.2f}%")

if __name__ == '__main__':
    benchmark()
