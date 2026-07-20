# -*- coding: utf-8 -*-
"""
Fix: Email rotator stats file uses relative path -> lost on restart.
Also add logging instead of silent failure.
"""
with open('core/email_rotator_pool.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_inspected = False
# Make sure pathlib is imported
# Path import already added at top-level

# Fix 1: _stats_file relative -> absolute
old1 = '        self._stats_file = "cache/email_rotator_stats.json"'
new1 = '        self._stats_file = str(Path(__file__).parent.parent / "cache" / "email_rotator_stats.json")'

# Fix 2: _persist_stats: log errors instead of silent pass
old2 = '''    def _persist_stats(self) -> None:
        """Save daily send counts for crash recovery."""
        try:
            os.makedirs(os.path.dirname(self._stats_file), exist_ok=True)
            stats = {
                str(date.today()): {
                    client.account.name: client._sent_today for client in self._accounts
                }
            }
            with open(self._stats_file, "w") as f:
                json.dump(stats, f)
        except Exception:
            pass'''

new2 = '''    def _persist_stats(self) -> None:
        """Save daily send counts for crash recovery."""
        try:
            os.makedirs(os.path.dirname(self._stats_file), exist_ok=True)
            stats = {
                str(date.today()): {
                    client.account.name: client._sent_today for client in self._accounts
                }
            }
            with open(self._stats_file, "w") as f:
                json.dump(stats, f)
            logger.debug(f"[RotatorPool] Persisted stats: {stats}")
        except Exception as e:
            logger.warning(f"[RotatorPool] Failed to persist stats: {e}")'''

changes = 0
if old1 in content:
    content = content.replace(old1, new1)
    changes += 1
    print("Fixed _stats_file path!")
else:
    print("WARNING: _stats_file pattern not found!")

if old2 in content:
    content = content.replace(old2, new2)
    changes += 1
    print("Fixed _persist_stats logging!")
else:
    print("WARNING: _persist_stats pattern not found!")
    # Show what's there
    idx = content.find("def _persist_stats")
    if idx >= 0:
        print("Found at idx:", idx)
        print(repr(content[idx:idx+500]))

if changes > 0:
    with open('core/email_rotator_pool.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved! ({changes} changes)")
else:
    print("No changes made.")
