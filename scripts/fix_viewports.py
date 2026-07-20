#!/usr/bin/env python3
"""Surgically standardize viewport meta tags across all HTML templates.

Fixes:
1. Remove `user-scalable=no` (WCAG 1.4.4 zoom violation).
2. Normalize `maximum-scale=1.0` -> `maximum-scale=5.0`.
3. Add `maximum-scale=5.0` to head viewports lacking it (consistency).
4. Remove duplicate body viewports (only one viewport is valid HTML).
"""
import os
import re

ROOT = "web/templates"
VP_RE = re.compile(r'<meta\b[^>]*\bname="viewport"[^>]*>', re.IGNORECASE)
VP_RE_WS = re.compile(r'<meta\b[^>]*\bname="viewport"[^>]*>\s*\n?', re.IGNORECASE)

changed = []


def fix_head_viewport(tag: str) -> str:
    new = tag
    # 1. Strip user-scalable=no (with optional leading comma/space)
    new = re.sub(r'\s*,?\s*user-scalable=no', '', new, flags=re.IGNORECASE)
    if 'maximum-scale' not in new:
        # 3. Add maximum-scale=5.0 after initial-scale
        new = re.sub(r'(initial-scale=1\.0)', r'\1, maximum-scale=5.0', new, flags=re.IGNORECASE)
        new = re.sub(r'(initial-scale=1)(?=["\'])', r'\1.0, maximum-scale=5.0', new, flags=re.IGNORECASE)
    else:
        # 2. Normalize any maximum-scale value to 5.0
        new = re.sub(r'maximum-scale=[\d.]+', 'maximum-scale=5.0', new, flags=re.IGNORECASE)
    return new


for dirpath, _dirs, files in os.walk(ROOT):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        original = html

        matches = list(VP_RE.finditer(html))
        if not matches:
            continue

        # Fix the first (head) viewport
        first = matches[0]
        fixed = fix_head_viewport(first.group(0))
        if fixed != first.group(0):
            html = html[:first.start()] + fixed + html[first.end():]

        # 4. Remove duplicate viewports (all after the first)
        all_m = list(VP_RE_WS.finditer(html))
        removed = 0
        if len(all_m) > 1:
            for m in reversed(all_m[1:]):
                html = html[:m.start()] + html[m.end():]
                removed += 1

        if html != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            changed.append((path, removed))
            print(f"FIXED: {path} (duplicates removed: {removed})")

print(f"\nTOTAL FILES CHANGED: {len(changed)}")
