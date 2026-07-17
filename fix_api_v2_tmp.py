import re

p = "web/routers/api_v2.py"
s = open(p, encoding="utf-8").read()
# Remove the client-facing "error": str(e) leak inside campaign_stats_api fallback
new_s = re.sub(r',\s*\n\s*"error":\s*str\(e\)\s*\n(\s*)\}', r'\n\1}', s)
assert new_s != s, "PATTERN NOT FOUND - no change made"
open(p, "w", encoding="utf-8").write(new_s)
print("FIXED api_v2.py error leak")
