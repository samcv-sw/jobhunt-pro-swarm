"""Dump full Roo Code extension state"""
import sqlite3, json, os, shutil

db_src = r"C:\Users\samde\AppData\Roaming\Code\User\globalStorage\state.vscdb"
db_copy = r"C:\Users\samde\Desktop\state_copy.vscdb"
out_file = r"C:\Users\samde\Desktop\roo_state_full.json"

shutil.copy2(db_src, db_copy)
conn = sqlite3.connect(db_copy)
cursor = conn.execute("SELECT key, value FROM ItemTable WHERE key = ?", ("RooVeterinaryInc.roo-cline",))
row = cursor.fetchone()
conn.close()
os.remove(db_copy)

if row:
    key, val = row
    if isinstance(val, bytes):
        parsed = json.loads(val.decode('utf-8'))
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
        print(f"Written to {out_file}")
        print(f"Total keys: {len(parsed)}")
        # Print auto-approve related keys
        auto_keys = ['autoApprovalEnabled','alwaysAllowReadOnly','alwaysAllowReadOnlyOutsideWorkspace',
                     'alwaysAllowWrite','alwaysAllowWriteOutsideWorkspace','alwaysAllowWriteProtected',
                     'alwaysAllowMcp','alwaysAllowModeSwitch','alwaysAllowSubtasks',
                     'alwaysAllowExecute','alwaysAllowFollowupQuestions','followupAutoApproveTimeoutMs',
                     'allowedCommands','deniedCommands','requestDelaySeconds','writeDelayMs']
        for ak in auto_keys:
            if ak in parsed:
                print(f"  {ak}: {parsed[ak]}")
else:
    print("Key not found!")
