"""Dump Roo Code extension state from VS Code state.vscdb"""
import sqlite3, json, os

db_src = r"C:\Users\samde\AppData\Roaming\Code\User\globalStorage\state.vscdb"
db_copy = r"C:\Users\samde\Desktop\state_copy.vscdb"

# Copy DB to avoid locking issues
import shutil
shutil.copy2(db_src, db_copy)

conn = sqlite3.connect(db_copy)
cursor = conn.execute("SELECT key, value FROM ItemTable")
all_rows = cursor.fetchall()
conn.close()

os.remove(db_copy)

logger.debug(f"Total rows: {len(all_rows)}")

# Find roo-cline keys
for key, val in all_rows:
    if 'roo' in key.lower() or 'cline' in key.lower():
        logger.debug(f"\n=== {key} ===")
        if isinstance(val, bytes):
            try:
                parsed = json.loads(val.decode('utf-8'))
                if isinstance(parsed, dict):
                    # Print auto-approve related keys
                    auto_keys = ['autoApprovalEnabled','alwaysAllowReadOnly','alwaysAllowReadOnlyOutsideWorkspace',
                                 'alwaysAllowWrite','alwaysAllowWriteOutsideWorkspace','alwaysAllowWriteProtected',
                                 'alwaysAllowMcp','alwaysAllowModeSwitch','alwaysAllowSubtasks',
                                 'alwaysAllowExecute','alwaysAllowFollowupQuestions','followupAutoApproveTimeoutMs',
                                 'allowedCommands','deniedCommands']
                    for ak in auto_keys:
                        if ak in parsed:
                            logger.debug(f"  {ak}: {parsed[ak]}")
                    logger.debug(f"  Total keys: {len(parsed)}")
                else:
                    logger.debug(f"  Value: {str(val)[:300]}")
            except Exception as e:
                logger.debug(f"  Raw bytes: {len(val)} bytes")
        else:
            logger.debug(f"  Value: {str(val)[:300]}")
