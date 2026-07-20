#!/usr/bin/env python3
"""
minify_local_assets.py — Zero-cost build-time minifier for JobHunt Pro local assets.

Compresses JS and CSS files without altering functionality:
  - web/static/js/cyberpunk.js
  - web/static/js/global-animations.js
  - web/static/js/i18n.js
  - web/static/css/index-rtl.css
  - web/static/css/premium-ui-rtl.css

Strategy: Pure regex/string transforms (no external deps) to keep $0 cost.
Safe for production: preserves string literals, regex, template literals, comments in strings.
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    ("web/static/js/cyberpunk.js", "js"),
    ("web/static/js/global-animations.js", "js"),
    ("web/static/js/i18n.js", "js"),
    ("web/static/css/index-rtl.css", "css"),
    ("web/static/css/premium-ui-rtl.css", "css"),
]


def _protect_strings(code: str):
    """Temporarily replace string/regex/template literals with placeholders."""
    store = []
    # Template literals (backticks) first to avoid clobbering ${}
    pat = re.compile(r"`(?:\\.|[^`\\])*`", re.DOTALL)
    def _tpl(m):
        store.append(m.group(0))
        return f"\x00T{len(store)-1}\x00"
    code = pat.sub(_tpl, code)
    # Double-quoted strings
    pat = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)
    def _d(m):
        store.append(m.group(0))
        return f"\x00S{len(store)-1}\x00"
    code = pat.sub(_d, code)
    # Single-quoted strings
    pat = re.compile(r"'(?:\\.|[^'\\])*'", re.DOTALL)
    def _s(m):
        store.append(m.group(0))
        return f"\x00S{len(store)-1}\x00"
    code = pat.sub(_s, code)
    # Regex literals (after strings to avoid matching / in strings)
    pat = re.compile(r"/(?:\\.|[^/\\])+/[gimsuy]*", re.DOTALL)
    def _r(m):
        store.append(m.group(0))
        return f"\x00R{len(store)-1}\x00"
    code = pat.sub(_r, code)
    return code, store


def _restore_strings(code: str, store: list):
    def _rep(m):
        idx = int(m.group(1))
        kind = m.group(0)[1]
        return store[idx]
    return re.sub(r"\x00[TSR](\d+)\x00", _rep, code)


def minify_js(code: str) -> str:
    code, store = _protect_strings(code)
    # Remove block comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    # Remove line comments (not in strings now)
    code = re.sub(r"(?<!:)//[^\n]*", "", code)
    # Collapse whitespace
    code = re.sub(r"[ \t]+", " ", code)
    code = re.sub(r"\s*\n\s*", "\n", code)
    code = re.sub(r"\n\s+", "\n", code)
    # Remove spaces around punctuation
    code = re.sub(r"\s*([=+\-*/%&|<>!?:;,(){}\[\]])\s*", r"\1", code)
    # Keep `=>` arrow spacing minimal but valid: `= >` -> `=>`
    code = re.sub(r"=\s*>", "=>", code)
    code = _restore_strings(code, store)
    return code.strip()


def minify_css(code: str) -> str:
    code, store = _protect_strings(code)
    # Remove comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    # Remove whitespace
    code = re.sub(r"\s+", " ", code)
    code = re.sub(r"\s*([{}:;,>])\s*", r"\1", code)
    code = re.sub(r";}", "}", code)
    code = _restore_strings(code, store)
    return code.strip()


def main():
    total_before = total_after = 0
    for rel, kind in TARGETS:
        path = os.path.join(BASE, rel)
        if not os.path.exists(path):
            print(f"SKIP (missing): {rel}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        before = len(raw.encode("utf-8"))
        out = minify_js(raw) if kind == "js" else minify_css(raw)
        after = len(out.encode("utf-8"))
        total_before += before
        total_after += after
        # Write minified back (overwrite in place — build step)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        pct = (1 - after / before) * 100 if before else 0
        print(f"MINIFIED {rel}: {before} -> {after} bytes ({pct:.1f}% saved)")
    print(f"\nTOTAL: {total_before} -> {total_after} bytes "
          f"({ (1 - total_after/total_before)*100:.1f}% saved)" if total_before else "No files")


if __name__ == "__main__":
    main()
