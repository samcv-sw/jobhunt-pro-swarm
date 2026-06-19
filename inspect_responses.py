# -*- coding: utf-8 -*-
import re, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

files = {
    'dice': 'resp_4.html',
    'bing': 'resp_7.html',
    'wuzzuf': 'resp_8.html',
    'linkedin': 'resp_b3.html',
}

print("INSPECTING HTML RESPONSES\n" + "="*60)

for name, fname in files.items():
    with open(fname, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    # Remove problematic chars for printing
    safe = text.replace('\ufffd', '?')
    raw_first = safe[:600]
    contains_html = "<html" in text.lower() or "<!doctype" in text.lower()
    job_words = bool(re.search(r"job|position|hiring|candidate|vacancy|apply|lister", text, re.I))
    title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.DOTALL)
    title = title_match.group(1).strip()[:80] if title_match else "NO TITLE"
    meta_robots = re.search(r'<meta\s+name="robots".*?>', text, re.I)
    
    print(f"\n=== {name} ===")
    print(f"  Size: {len(text)} bytes")
    print(f"  Title: {title}")
    print(f"  Has html: {contains_html}")
    print(f"  Has job keywords: {job_words}")
    print(f"  Meta robots: {meta_robots.group(0)[:80] if meta_robots else 'NONE'}")
    print(f"  First 500 chars:")
    print(f"  {raw_first[:500]}")

# JSON results
print("\n\n" + "="*60)
print("FULL RESULTS TABLE")
print("="*60)
with open("job_source_test_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for s in data["sources"]:
    code = str(s.get("http_code", "?"))
    length = str(s.get("content_length", 0))
    has_job = str(s.get("has_job_content", False))
    n = s['name']
    print(f"  {n:25s} | HTTP {code:3s} | {length:>6s}B | job={has_job:5s}")

print(f"\nWORKING: {len(data['working'])} | FAILED: {len(data['failed'])} | TOTAL: {len(data['sources'])}")
