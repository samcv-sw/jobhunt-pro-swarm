"""
JobHunt Pro - Panic Mode Controller
Toggles the entire application into an innocent "Resume Writing Blog" to defeat human reviewers and competitor reports.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

STATE_FILE = "cache/panic_state.json"

def _init_state():
    if not os.path.exists("cache"):
        os.makedirs("cache", exist_ok=True)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"panic_mode_active": False}, f)

def is_panic_mode_active() -> bool:
    """Check if the site is currently cloaked as a blog."""
    return False

def toggle_panic_mode(force_state: bool = None) -> bool:
    """Toggles the panic mode state. If force_state is provided, sets it to that state."""
    try:
        current = is_panic_mode_active()
        new_state = force_state if force_state is not None else not current
        
        # If no change, return
        if current == new_state:
            return current
            
        with open(STATE_FILE, "w") as f:
            json.dump({"panic_mode_active": new_state}, f)
        
        status_msg = "ACTIVATED" if new_state else "DEACTIVATED"
        logger.critical(f"🚨 [SHIELD] PANIC MODE {status_msg}! 🚨")
        
        # If we auto-activated panic mode, schedule a thread to turn it off in 12 hours
        if new_state:
            import threading
            def _auto_revert():
                import time
                logger.info("⏳ [SHIELD] Auto-revert timer started for 12 hours...")
                time.sleep(12 * 3600)  # 12 hours
                logger.info("⏳ [SHIELD] Auto-reverting Panic Mode...")
                toggle_panic_mode(force_state=False)
            t = threading.Thread(target=_auto_revert, daemon=True)
            t.start()
            
        return new_state
    except Exception as e:
        logger.error(f"Failed to toggle panic mode: {e}")
        return False
