"""Telegram Bot Watchdog — 24/7 auto-restart, truly infinite."""
import subprocess, sys, time, os, signal

PROJ = r"C:\Users\samde\Desktop\cv sam new ma3 kimi"
BOT = os.path.join(PROJ, "run_tg_local.py")
LOG = os.path.join(PROJ, "bot_watchdog.log")
LOCK = os.path.join(PROJ, "bot_watchdog.lock")

# Prevent double watchdog
if os.path.exists(LOCK):
    try:
        with open(LOCK) as f:
            old_pid = int(f.read().strip())
        # Check if old watchdog is still alive
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(1, False, old_pid)  # PROCESS_TERMINATE
        if handle:
            kernel32.TerminateProcess(handle, 0)
            kernel32.CloseHandle(handle)
            time.sleep(2)
    except Exception:
        pass

with open(LOCK, "w") as f:
    f.write(str(os.getpid()))

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        # Keep log under 5MB
        if os.path.getsize(LOG) > 5_000_000:
            with open(LOG, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(LOG, "w", encoding="utf-8") as f:
                f.writelines(lines[-500:])
    except Exception:
        pass

log("=" * 50)
log("Watchdog starting (PID: %d)..." % os.getpid())

# Kill stale bot instances (not ourselves) — uses external PS1 to avoid  escaping issues
mypid = os.getpid()
try:
    out = subprocess.check_output(
        ['powershell', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(PROJ, 'kill_stale_bots.ps1'), '-Mypid', str(mypid)],
        shell=False, text=True, timeout=15
    )
    for line in out.splitlines():
        line = line.strip()
        if line:
            log(line)
    time.sleep(2)
except Exception as e:
    log(f"Cleanup scan issue (non-critical): {e}")

restarts = 0
consecutive_crashes = 0
last_success_time = time.time()

while True:  # TRULY INFINITE — no limit
    restarts += 1
    log(f"=== Bot run #{restarts} ===")
    
    proc = subprocess.Popen(
        [sys.executable, BOT],
        cwd=PROJ,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait with heartbeat logging
    start = time.time()
    while proc.poll() is None:
        time.sleep(30)
        elapsed = time.time() - start
        if elapsed > 3600:  # Bot running >1hr healthy
            consecutive_crashes = 0
            last_success_time = time.time()
    
    rc = proc.returncode
    runtime = time.time() - start
    
    if rc == 0:
        log(f"Bot exited cleanly after {runtime:.0f}s. Restarting in 5s...")
        consecutive_crashes = 0
        time.sleep(5)
    else:
        consecutive_crashes += 1
        backoff = min(consecutive_crashes * 5, 60)  # Max 60s backoff
        log(f"Bot crashed (code {rc}) after {runtime:.0f}s. Crash #{consecutive_crashes}, restarting in {backoff}s...")
        
        # Log crash output
        try:
            stdout, stderr = proc.communicate(timeout=1)
            if stderr:
                log(f"Bot stderr: {stderr.decode('utf-8', errors='replace')[:500]}")
        except Exception:
            pass
        
        time.sleep(backoff)
    
    # Health check: if bot ran <10s and crashed 3x, something is broken
    if runtime < 10 and consecutive_crashes >= 3:
        log("CRITICAL: Bot crashing instantly 3x. Waiting 2 min before retry...")
        time.sleep(120)

log("Watchdog exiting")
try:
    os.remove(LOCK)
except Exception:
    pass
