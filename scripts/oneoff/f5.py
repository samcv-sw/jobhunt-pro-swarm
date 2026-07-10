with open('core/email_rotator_pool.py', 'rb') as f:
    raw = f.read()

changes = []

# Fix 1: _stats_file relative -> absolute
old1 = b'        self._stats_file = "cache/email_rotator_stats.json"'
new1 = b'        self._stats_file = str(Path(__file__).parent.parent / "cache" / "email_rotator_stats.json")'
if old1 in raw:
    raw = raw.replace(old1, new1)
    changes.append('_stats_file fixed')
else:
    print('WARNING: _stats_file not found')

# Fix 2: _persist_stats silent pass -> log warning
old2 = b'        except Exception:\n            pass'
new2 = b'        except Exception as e:\n            logger.warning(f"[RotatorPool] Failed to persist stats: {e}")'
if old2 in raw:
    raw = raw.replace(old2, new2)
    changes.append('_persist_stats logging fixed')
else:
    print('WARNING: silent pass not found')

if changes:
    with open('core/email_rotator_pool.py', 'wb') as f:
        f.write(raw)
    print('Done:', changes)
else:
    print('Nothing changed!')
