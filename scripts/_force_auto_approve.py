"""
FORCE AUTO-APPROVE FOR ROO CODE
Directly modifies VS Code's state.vscdb to enable ALL auto-approve settings permanently.
This bypasses the UI and writes directly to the extension's globalState storage.
"""
import sqlite3
import json
import shutil
import os
import sys

DB_SRC = os.path.expandvars(r"%APPDATA%\Code\User\globalStorage\state.vscdb")
DB_COPY = os.path.expandvars(r"%USERPROFILE%\Desktop\state_edit.vscdb")

# Step 1: Copy DB (VS Code locks the original)
shutil.copy2(DB_SRC, DB_COPY)

# Step 2: Read current state
conn = sqlite3.connect(DB_COPY)
cursor = conn.execute("SELECT key, value FROM ItemTable WHERE key = ?", ("RooVeterinaryInc.roo-cline",))
row = cursor.fetchone()

if not row:
    print("ERROR: RooVeterinaryInc.roo-cline key not found in DB!")
    conn.close()
    os.remove(DB_COPY)
    sys.exit(1)

key, val = row
if isinstance(val, bytes):
    state = json.loads(val.decode('utf-8'))
else:
    state = json.loads(val)

print(f"Current state has {len(state)} keys")

# Step 3: Set ALL auto-approve settings to True
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
    "followupAutoApproveTimeoutMs": 0,  # Instant auto-approve
    "requestDelaySeconds": 0,  # No delay between requests
    "writeDelayMs": 0,  # No write delay
}

for k, v in auto_settings.items():
    old_val = state.get(k, "NOT SET")
    state[k] = v
    print(f"  {k}: {old_val} -> {v}")

# Also ensure allowedCommands has * (allow all)
state["allowedCommands"] = ["*"]
state["deniedCommands"] = []

# Step 4: Write back
new_val = json.dumps(state).encode('utf-8')
conn.execute("UPDATE ItemTable SET value = ? WHERE key = ?", (new_val, key))
conn.commit()
conn.close()

# Step 5: Copy back to original location
shutil.copy2(DB_COPY, DB_SRC)
os.remove(DB_COPY)

print("")
print("ALL AUTO-APPROVE SETTINGS ENABLED PERMANENTLY!")
print("These settings survive PC restarts because they're stored in VS Code's globalState DB.")
print("")
print("Changes applied:")
for k in auto_settings:
    print(f"  [OK] {k} = True")
print("  [OK] allowedCommands = ['*']")
print("  [OK] deniedCommands = []")
