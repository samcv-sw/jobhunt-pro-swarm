# Adversarial Review — Database Pool Recycling & Connection Warmer

## Challenge Summary

**Overall risk assessment**: LOW

The database pool recycling and connection warmer design is robust and incorporates redundant defense-in-depth measures. Below are identified edge cases, assumptions, and their corresponding blast radius.

## Challenges

### [Low] Challenge 1: Connection Recycling Under Clock Drift / High Latency
- **Assumption challenged**: The time difference `now - conn.created_at` will always detect expired connections correctly.
- **Attack scenario**: If the server clock drifts backwards, connections might be considered "negative" age or fail to trigger recycling. If thread context switching or CPU starvation delays execution significantly, connections could become stale immediately after checkout.
- **Blast radius**: The connection could be stale when the actual query runs.
- **Mitigation**: The pre-ping (`SELECT 1`) runs immediately after the recycling check. Even if clock drift skips the recycling block, the pre-ping query will execute and throw a connection failure, forcing discarding and retry.

### [Low] Challenge 2: Performance Overhead of Pre-Ping
- **Assumption challenged**: Querying `SELECT 1` on every checkout is negligible.
- **Attack scenario**: Under extremely high connection checkout throughput (e.g. thousands of checkouts per second), executing `SELECT 1` on every checkout adds an extra database round-trip (1 RTT to Neon database, e.g. 10ms-50ms).
- **Blast radius**: Increased transaction/endpoint latency.
- **Mitigation**: Since this is a serverless application where Neon cold starts and idle suspensions are the primary reliability issues, the trade-off of minor query latency in favor of absolute reliability is highly appropriate.

---

## Stress Test Results

- **Expired connection checkout** → Connection discarded, fresh connection returned → **PASS**
- **Pre-ping failure** → Stale connection discarded, wrapper retries, fresh connection returned → **PASS**
- **Max retry exhaustion on pre-ping** → Correctly raises `OperationalError` after 5 failures → **PASS**
