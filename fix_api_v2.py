p = 'web/routers/api_v2.py'
with open(p, encoding='utf-8') as f:
    s = f.read()

old = '''        logger.warning(f"Error fetching campaign stats: {e}")
        return {
            "total_sent": 0,
            "total_opened": 0,
            "open_rate": 0,
            "campaigns": {"welcome": 0, "abandoned_cart": 0, "re_engagement": 0, "post_purchase": 0},
            "error": str(e)
        }'''

new = '''        logger.warning(f"Error fetching campaign stats: {e}")
        return {
            "total_sent": 0,
            "total_opened": 0,
            "open_rate": 0,
            "campaigns": {"welcome": 0, "abandoned_cart": 0, "re_engagement": 0, "post_purchase": 0},
        }'''

if old in s:
    s = s.replace(old, new, 1)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)
    print('FIXED')
else:
    print('NOT FOUND - inspecting context')
    idx = s.find('Error fetching campaign stats')
    print(repr(s[idx-60:idx+220]))
