#!/usr/bin/env python3
"""Identify which modified .html files in web/templates have ONLY viewport-related
git diff changes (so they can be surgically committed without the 73 unrelated
pre-existing modifications).

A file is included iff EVERY added/removed diff line contains 'name="viewport"'.
"""
import subprocess
import sys

ROOT = "web/templates"


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True,
        encoding="utf-8", errors="replace"
    ).stdout


def main():
    # List modified html files
    out = git("diff", "--name-only", "--", f"{ROOT}/*.html", f"{ROOT}/**/*.html")
    files = [f for f in out.splitlines() if f.endswith(".html")]
    # Also catch en/ and ar/ subdirs (git glob above may miss nested)
    out2 = git("diff", "--name-only")
    files = list({f for f in out2.splitlines() if f.startswith(ROOT) and f.endswith(".html")})

    included = []
    excluded = []
    for f in files:
        diff = git("diff", "--", f)
        lines = diff.splitlines()
        viewport_only = True
        for ln in lines:
            if ln.startswith("+++") or ln.startswith("---") or ln.startswith("@@"):
                continue
            if ln.startswith("+") or ln.startswith("-"):
                if 'name="viewport"' not in ln:
                    viewport_only = False
                    break
        if viewport_only:
            included.append(f)
        else:
            excluded.append(f)

    print(f"TOTAL MODIFIED HTML: {len(files)}")
    print(f"VIEWPORT-ONLY (safe to commit): {len(included)}")
    print(f"HAS OTHER CHANGES (exclude): {len(excluded)}")
    print("\n--- INCLUDED (viewport-only) ---")
    for f in sorted(included):
        print(f)
    print("\n--- EXCLUDED (other changes) ---")
    for f in sorted(excluded):
        print(f)


if __name__ == "__main__":
    main()
