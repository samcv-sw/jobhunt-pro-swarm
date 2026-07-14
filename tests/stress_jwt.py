import importlib
import os
import sys
import time

import jwt

# Add parent directory to path so we can import backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import backend.auth as auth


def run_empty_keys_tests():
    print("--- Test 1: Empty / Whitespace-only keys ---")

    # We will test using monkeypatch-like manual env updates and module reloads
    original_env_keys = os.environ.get("JWT_SECRET_KEYS")
    original_env_key = os.environ.get("JWT_SECRET_KEY")

    try:
        # Case 1.1: whitespace-only keys
        os.environ["JWT_SECRET_KEYS"] = "   ,   ,   "
        os.environ["JWT_SECRET_KEY"] = "default_fallback_key"
        importlib.reload(auth)
        print(f"Whitespace-only list parsed keys: {auth.JWT_SECRET_KEYS}")
        assert auth.JWT_SECRET_KEYS == ["default_fallback_key"], "Should fallback to JWT_SECRET_KEY"

        # Case 1.2: completely empty list
        os.environ["JWT_SECRET_KEYS"] = ""
        os.environ["JWT_SECRET_KEY"] = "default_fallback_key_2"
        importlib.reload(auth)
        print(f"Empty list parsed keys: {auth.JWT_SECRET_KEYS}")
        assert auth.JWT_SECRET_KEYS == ["default_fallback_key_2"], "Should fallback to JWT_SECRET_KEY"

        # Case 1.3: both empty/missing (testing fallback default)
        if "JWT_SECRET_KEYS" in os.environ:
            del os.environ["JWT_SECRET_KEYS"]
        if "JWT_SECRET_KEY" in os.environ:
            del os.environ["JWT_SECRET_KEY"]
        os.environ["TESTING"] = "true"
        importlib.reload(auth)
        print(f"Both missing parsed keys: {auth.JWT_SECRET_KEYS}")
        assert auth.JWT_SECRET_KEYS == ["jobhunt-pro-secret-key-32bytes-ok!!"], "Should fallback to TESTING default key"

        print("Verdict: PASS")
    except Exception as e:
        print(f"Verdict: FAIL - {e}")
        raise e
    finally:
        # Restore environment
        if original_env_keys is not None:
            os.environ["JWT_SECRET_KEYS"] = original_env_keys
        elif "JWT_SECRET_KEYS" in os.environ:
            del os.environ["JWT_SECRET_KEYS"]

        if original_env_key is not None:
            os.environ["JWT_SECRET_KEY"] = original_env_key
        elif "JWT_SECRET_KEY" in os.environ:
            del os.environ["JWT_SECRET_KEY"]
        importlib.reload(auth)

def run_performance_latency_tests():
    print("\n--- Test 2: Validation Latency with 20+ Keys ---")

    # Generate 50 keys
    keys = [f"secret_key_{i:04d}_for_testing_jwt_rotation_performance_purposes" for i in range(100)]
    auth.JWT_SECRET_KEYS = keys
    auth.JWT_SECRET_KEY = keys[0]

    payload = {"sub": "user_stress_test", "role": "admin"}

    # We will test decoding tokens signed with:
    # 1. 1st key (primary)
    # 2. 10th key
    # 3. 20th key
    # 4. 50th key
    # 5. 100th key
    # 6. Invalid key (forces iterating all 100 keys)

    tokens = {
        "1st key": jwt.encode(payload, keys[0], algorithm="HS256"),
        "10th key": jwt.encode(payload, keys[9], algorithm="HS256"),
        "20th key": jwt.encode(payload, keys[19], algorithm="HS256"),
        "50th key": jwt.encode(payload, keys[49], algorithm="HS256"),
        "100th key": jwt.encode(payload, keys[99], algorithm="HS256"),
        "invalid key": jwt.encode(payload, "completely_unknown_key", algorithm="HS256")
    }

    iterations = 2000
    print(f"Running {iterations} decodes per scenario...")

    results = {}
    for name, token in tokens.items():
        start_time = time.perf_counter()
        success_count = 0
        failure_count = 0

        for _ in range(iterations):
            try:
                auth.decode_jwt_token(token)
                success_count += 1
            except jwt.InvalidSignatureError:
                failure_count += 1
            except Exception as e:
                print(f"Unexpected exception for {name}: {type(e).__name__}: {e}")

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_us = (total_time_ms / iterations) * 1000

        results[name] = {
            "total_ms": total_time_ms,
            "avg_us": avg_time_us,
            "success": success_count,
            "failed": failure_count
        }
        print(f"  {name:12s}: Total {total_time_ms:6.2f} ms | Avg {avg_time_us:6.2f} us | Success: {success_count} | Failed: {failure_count}")

    # Analyze if there's an linear increase in verification latency
    # Iterating 100 keys vs 1 key: does it scale linearly?
    # jwt.decode HS256 is fast (~5-15 us on modern CPUs), so 100 HMAC iterations should take <1 ms.
    # Let's verify if the overhead is acceptable.
    # An invalid key takes the longest because it checks all 100 keys.
    print("\nLatency Analysis:")
    avg_1st = results["1st key"]["avg_us"]
    avg_invalid = results["invalid key"]["avg_us"]
    overhead_per_key = (avg_invalid - avg_1st) / len(keys)
    print(f"  Average overhead per key evaluated: {overhead_per_key:.4f} us")
    print(f"  Total validation time for invalid token under 100 keys: {avg_invalid:.2f} us ({avg_invalid/1000:.4f} ms)")

    assert results["1st key"]["success"] == iterations
    assert results["50th key"]["success"] == iterations
    assert results["invalid key"]["failed"] == iterations
    print("Verdict: PASS")

def run_malformed_token_tests():
    print("\n--- Test 3: Malformed JWT token handling ---")

    # Setup standard keys
    auth.JWT_SECRET_KEYS = ["key_primary", "key_secondary"]

    malformed_tokens = [
        "not-a-token-at-all",
        "header.payload.signature.extra_part",
        "header.payload",  # missing signature part
        "",
        None
    ]

    try:
        for token in malformed_tokens:
            start_time = time.perf_counter()
            try:
                auth.decode_jwt_token(token)
                print(f"  Token {repr(token)}: unexpectedly decoded successfully!")
                assert False, "Should have failed decoding"
            except jwt.InvalidTokenError as e:
                duration_us = (time.perf_counter() - start_time) * 1000000
                print(f"  Token {repr(token)}: correctly raised InvalidTokenError ({type(e).__name__}) in {duration_us:.1f} us")
            except Exception as e:
                print(f"  Token {repr(token)}: raised unexpected exception: {type(e).__name__}: {e}")
                assert False, f"Unexpected exception type: {type(e).__name__}"

        # Test algorithm confusion (e.g. RS256 token under HS256)
        print("  Testing Algorithm Confusion (token signed with RS256 but backend expects HS256)...")
        # Generate a mock RS256 token (or we can just forge one with HS256 header claims changed)
        # Standard PyJWT will reject if algorithm doesn't match list of allowed algorithms.
        # Let's forge a token header claiming "alg": "none" or "alg": "RS256"
        payload = {"sub": "user_confuse"}
        token_none = jwt.encode(payload, "", algorithm=None)

        try:
            auth.decode_jwt_token(token_none)
            assert False, "Token with alg=none should be rejected"
        except jwt.InvalidTokenError as e:
            print(f"  Token with alg=none correctly rejected: {e}")

        print("Verdict: PASS")
    except Exception as e:
        print(f"Verdict: FAIL - {e}")
        raise e

def run_dynamic_keys_tests():
    print("\n--- Test 4: Dynamic environment variable changes ---")

    # Read the current module variables
    initial_keys_in_module = list(auth.JWT_SECRET_KEYS)

    # 1. Update os.environ
    os.environ["JWT_SECRET_KEYS"] = "new_dynamic_key_1, new_dynamic_key_2"

    # 2. Check if the module auto-updates
    keys_after_env_change = list(auth.JWT_SECRET_KEYS)

    print(f"  Module keys before env change: {initial_keys_in_module}")
    print(f"  Module keys after env change:  {keys_after_env_change}")

    # Let's check if they are identical (they should be, since variables are evaluated at import time)
    is_static = (initial_keys_in_module == keys_after_env_change)
    print(f"  Are keys static (loaded once at import)? {is_static}")

    if is_static:
        print("  [INFO] Verification keys are loaded statically at import/startup time.")
        print("         This is normal for Python modules but means env changes require reload/restart.")
    else:
        print("  [WARNING] Verification keys are dynamic. (This is unexpected based on current implementation).")

    print("Verdict: PASS")

if __name__ == "__main__":
    print("====================================================")
    print("      JWT SECRET ROTATION EMPIRICAL STRESS TEST     ")
    print("====================================================")

    run_empty_keys_tests()
    run_performance_latency_tests()
    run_malformed_token_tests()
    run_dynamic_keys_tests()

    print("====================================================")
    print("Stress test execution completed successfully.")
    print("====================================================")
