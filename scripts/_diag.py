"""Parse pytest_full.txt and emit compact per-test failure diagnostics."""
import re

PATH = "pytest_full.txt"
with open(PATH, "r", encoding="utf-8", errors="replace") as fh:
    lines = fh.readlines()

# Locate FAILURES section
start = None
end = None
for i, ln in enumerate(lines):
    if "FAILURES" in ln and "=" in ln:
        start = i
    if "short test summary" in ln:
        end = i
        break

if start is None:
    print("NO FAILURES SECTION FOUND")
    raise SystemExit(0)

section = lines[start:end if end else len(lines)]

# Split into per-test blocks on header lines like:  _______ test_x _______
header_re = re.compile(r"^_+ .+ _+\s*$")
cur = None
blocks = {}
order = []
for ln in section:
    if header_re.match(ln.strip()):
        cur = ln.strip().strip("_ ").strip()
        blocks[cur] = []
        order.append(cur)
        continue
    if cur is not None:
        blocks[cur].append(ln.rstrip("\n"))

for name in order:
    blk = blocks[name]
    # Extract E  error lines and location lines
    errs = [l for l in blk if l.startswith("E  ")]
    locs = [l for l in blk if re.search(r"\.py:\d+: in ", l)]
    print("=" * 70)
    print("TEST:", name)
    for l in locs[:4]:
        print("  LOC:", l.strip())
    for e in errs[:6]:
        print("  ERR:", e[2:].strip())
    # Also print any non-empty code-ish lines near assertion
    for l in blk:
        s = l.strip()
        if s.startswith("assert ") or "AssertionError" in s or "KeyError" in s or "TypeError" in s or "ValueError" in s:
            if s not in [e[2:].strip() for e in errs]:
                print("  CODE:", s[:160])

print("=" * 70)
print("TOTAL FAILURES PARSED:", len(order))
