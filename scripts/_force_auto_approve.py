"""
FORCE AUTO-APPROVE FOR ROO CODE (VS CODE & ANTIGRAVITY IDE)
Directly modifies the state.vscdb to enable ALL auto-approve settings permanently.
"""
import json
import logging
import os
import shutil
import sqlite3
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DB_PATHS = [
    os.path.expandvars(r"%APPDATA%\Code\User\globalStorage\state.vscdb"),
    os.path.expandvars(r"%APPDATA%\Antigravity IDE\User\globalStorage\state.vscdb")
]

DB_COPY = os.path.expandvars(r"%USERPROFILE%\Desktop\state_edit.vscdb")

def force_auto_approve(db_src):
    if not os.path.exists(db_src):
        logger.info(f"Database not found: {db_src}, skipping.")
        return False

    logger.info(f"Processing database: {db_src}")
    try:
        shutil.copy2(db_src, DB_COPY)
        conn = sqlite3.connect(DB_COPY)
        cursor = conn.execute("SELECT key, value FROM ItemTable WHERE key = ?", ("RooVeterinaryInc.roo-cline",))
        row = cursor.fetchone()

        if not row:
            logger.info("  WARNING: RooVeterinaryInc.roo-cline key not found in this DB! Skipping.")
            conn.close()
            if os.path.exists(DB_COPY):
                os.remove(DB_COPY)
            return False

        key, val = row
        if isinstance(val, bytes):
            state = json.loads(val.decode('utf-8'))
        else:
            state = json.loads(val)

        logger.info(f"  Current state has {len(state)} keys")

        auto_settings = {
            "autoApprovalEnabled": True,
            "alwaysAllowReadOnly": True,
            "alwaysAllowReadOnlyOutsideWorkspace": True,
            "alwaysAllowWrite": True,
            "alwaysAllowWriteOutsideWorkspace": True,
            "alwaysAllowWriteProtected": True,
            "alwaysAllowMcp": True,
            "alwaysAllowModeSwitch": True,
            "alwaysAllowSubtasks": True,
            "alwaysAllowExecute": True,
            "alwaysAllowFollowupQuestions": True,
            "followupAutoApproveTimeoutMs": 0,
            "requestDelaySeconds": 0,
            "writeDelayMs": 0,
        }

        for k, v in auto_settings.items():
            old_val = state.get(k, "NOT SET")
            state[k] = v
            logger.info(f"    {k}: {old_val} -> {v}")

        state["allowedCommands"] = ["*"]
        state["deniedCommands"] = []

        new_val = json.dumps(state).encode('utf-8')
        conn.execute("UPDATE ItemTable SET value = ? WHERE key = ?", (new_val, key))
        conn.commit()
        conn.close()

        shutil.copy2(DB_COPY, db_src)
        if os.path.exists(DB_COPY):
            os.remove(DB_COPY)
        logger.info("  Successfully updated auto-approve settings!")
        return True
    except Exception as e:
        logger.info(f"  Error processing database: {e}")
        if os.path.exists(DB_COPY):
            os.remove(DB_COPY)
        return False

def main():
    updated_any = False
    for path in DB_PATHS:
        if force_auto_approve(path):
            updated_any = True
    
    if updated_any:
        logger.info("\nALL AUTO-APPROVE SETTINGS ENABLED PERMANENTLY!")
        logger.info("These settings survive IDE restarts because they're stored in globalState DB.")
    else:
        logger.info("\nNo databases were updated.")

if __name__ == "__main__":
    main()
