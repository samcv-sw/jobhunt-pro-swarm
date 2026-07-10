with open('core/email_rotator_pool.py', 'rb') as f:
    raw = f.read()

# CRLF line endings - find the except/pass in _persist_stats
old = b'except Exception:\r\n            pass'
new = b'except Exception as e:\r\n            logger.warning("[RotatorPool] Failed to persist stats: " + str(e))'

if old in raw:
    raw = raw.replace(old, new)
    with open('core/email_rotator_pool.py', 'wb') as f:
        f.write(raw)
    print('Fixed!')
else:
    print('Not found')
