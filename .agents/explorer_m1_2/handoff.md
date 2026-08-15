# Handoff Report: Milestone M1 (Feature 2 - Container RSS Memory Supervisor)

**Agent**: Explorer 2 (Replacement)  
**Recipient**: Parent Orchestrator (`sub_orch_m1_1` / `41011934-7311-4236-891c-edf1863f8340`)  
**Milestone**: M1 (R1: 24/7 Zero-Cost Cloud & Immortality Keepalive)  
**Subject**: In-depth Investigation & Recommendations for `start_cloud.py` RSS Memory Supervisor  

---

## 1. Observation

1. **Supervisor Process Entrypoint & GC Tuning**:
   - `start_cloud.py:18`: `gc.set_threshold(50, 5, 5)` configures aggressive GC tuning for the parent supervisor.
   - `start_cloud.py:253`: `gc.collect()` is explicitly invoked every loop iteration.
2. **Process Tree Memory Measurement**:
   - `start_cloud.py:256-264`: Supervisor retrieves `psutil` via `sys.modules.get("psutil")` and aggregates parent RSS: `total_rss += psutil.Process(os.getpid()).memory_info().rss`.
   - `start_cloud.py:277-285`: For each service in `running_services`, queries `proc_info = psutil.Process(p.pid)` and recursively loops through children:
     ```python
     for child in proc_info.children(recursive=True):
         rss += child.memory_info().rss
     ```
3. **Two-Tier Threshold Enforcement**:
   - **Tier 1 (Per-Service Ceiling)**: `start_cloud.py:289-300`:
     ```python
     if rss > service["limit"]:
         logger.warning(f"Service '{name}' (PID {p.pid}) RSS ({rss / (1024*1024):.1f}MB) exceeded limit of {service['limit'] / (1024*1024):.1f}MB! Recycling service...")
         p.terminate()
         try:
             p.wait(timeout=5)
         except subprocess.TimeoutExpired:
             p.kill()
             p.wait()
     ```
     Limits: Celery = 180MB, Sync Worker = 80MB, Uvicorn/Granian = 220MB.
   - **Tier 2 (Global Container 450MB Ceiling)**: `start_cloud.py:305-337`:
     ```python
     if psutil and total_rss > 450 * 1024 * 1024:
         ...
         # Finds largest consumer in running_services and calls terminate() / wait(5) / kill()
     ```
4. **Test Suite Coverage**:
   - Grep search for `start_cloud` across `tests/` yielded **0 results**.
   - Grep search for `450` across `tests/` yielded **0 results**.
   - `tests/test_auto_heal.py` only tests the `/api/system/auto-heal` endpoint mocks, not the container memory supervisor.
5. **Coupling in `start_cloud.py`**:
   - All memory evaluation, process tree aggregation, and recycling logic are tightly coupled inside the infinite `while True` loop of `launch_services()` (lines 251–340).

---

## 2. Logic Chain

1. **Premise 1 (From Obs 1, 2, 3)**: The core algorithmic concepts required by Acceptance Criterion 2 (`start_cloud.py` includes RSS monitor thread/loop checking total process tree RAM, triggers graceful GC/recycle when RSS exceeds 450MB, targeting highest consumer) are present in `start_cloud.py`.
2. **Premise 2 (From Obs 4)**: Despite the implementation existing in `start_cloud.py`, there is zero test coverage in `tests/` verifying memory ceiling breaches, process tree aggregation, or largest-consumer recycling.
3. **Premise 3 (From Obs 5)**: Because `launch_services()` is an infinite loop that directly calls `subprocess.Popen` and `time.sleep(5)`, it cannot be tested in unit tests without refactoring the memory evaluation and recycling logic into discrete, testable helper functions.
4. **Premise 4 (From Obs 2, 3)**: There is an edge case where killing a service in Tier 1 leaves `total_rss` elevated during the same tick, potentially triggering Tier 2 and terminating a second healthy service. Additionally, `proc_info.children(recursive=True)` can raise `NoSuchProcess` if children exit concurrently during traversal.
5. **Conclusion**: To satisfy Milestone M1 Feature 2 requirements robustly, `start_cloud.py` must be modularized into testable functions (`get_process_tree_rss`, `evaluate_memory_and_enforce`, `terminate_and_recycle`), race conditions guarded, and a dedicated test file `tests/test_memory_supervisor.py` added to the test suite.

---

## 3. Caveats

- **Host vs Container Memory**: `psutil.Process().memory_info().rss` measures user-space process tree RSS. In container environments with strict cgroups v1/v2 limits (like Render), total cgroup memory may include kernel slab cache. However, process tree RSS is the standard and safest portable metric for worker recycling without requiring root/cgroup file system privileges.
- **Windows vs Linux Celery Execution**: On Windows (`os.name == 'nt'`), Celery runs with `-P solo`. Process tree recursion handles both single-process solo and Linux pre-fork worker pool process trees cleanly.

---

## 4. Conclusion

The Container RSS memory supervisor logic in `start_cloud.py` is structurally sound in design but requires:
1. **Refactoring into modular functions** for clean unit testing and eliminating race conditions / double-recycling edge cases.
2. **Immediate respawn after termination** to eliminate the 5-second downtime window.
3. **Implementation of `tests/test_memory_supervisor.py`** to achieve 100% test coverage for all supervisor memory limits, process tree calculation, GC invocation, and largest consumer recycling.

Detailed code designs and recommendations are documented in:
`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_2\analysis.md`

---

## 5. Verification Method

1. **Execute New Test Suite**:
   ```bash
   pytest tests/test_memory_supervisor.py -v
   ```
2. **Verify Full Test Suite Health**:
   ```bash
   pytest tests/
   ```
3. **Code Inspection**:
   - Inspect `start_cloud.py` for extracted functions: `get_process_tree_rss()`, `terminate_and_recycle()`, and `evaluate_memory_and_enforce()`.
   - Verify `tests/test_memory_supervisor.py` covers:
     - Process tree RSS aggregation
     - Per-service memory threshold recycling
     - Global 450MB container ceiling targeting the largest consumer
     - Transient child process exit handling (`NoSuchProcess` / `ZombieProcess`)
     - `gc.collect()` and threshold tuning verification
