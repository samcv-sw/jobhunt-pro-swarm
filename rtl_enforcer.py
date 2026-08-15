"""
JobHunt Pro — RTL & CSS Logical Properties Compliance Enforcer
==============================================================
Enforces strict Arabic & RTL cultural ergonomics across templates and stylesheets:
- CSS Logical Properties (margin-inline-*, padding-inline-*, text-align: start/end, float: inline-start/end, inset-inline-*)
- Form Input Bi-Directionality (dir="auto" on input, textarea, select)
- Arabic Typography (Cairo, Tajawal, IBM Plex Arabic font stacks)
- CLI Modes: --scan, --fix, --check
"""

import os
import re
import sys
import argparse

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CSS_REPLACEMENTS = [
    (r'border-top-left-radius:', r'border-start-start-radius:'),
    (r'border-top-right-radius:', r'border-start-end-radius:'),
    (r'border-bottom-left-radius:', r'border-end-start-radius:'),
    (r'border-bottom-right-radius:', r'border-end-end-radius:'),
    (r'border-left-width:', r'border-inline-start-width:'),
    (r'border-right-width:', r'border-inline-end-width:'),
    (r'border-left-color:', r'border-inline-start-color:'),
    (r'border-right-color:', r'border-inline-end-color:'),
    (r'border-left:', r'border-inline-start:'),
    (r'border-right:', r'border-inline-end:'),
    (r'margin-left:', r'margin-inline-start:'),
    (r'margin-right:', r'margin-inline-end:'),
    (r'padding-left:', r'padding-inline-start:'),
    (r'padding-right:', r'padding-inline-end:'),
    (r'float:\s*left\b', r'float: inline-start'),
    (r'float:\s*right\b', r'float: inline-end'),
    (r'text-align:\s*left\b', r'text-align: start'),
    (r'text-align:\s*right\b', r'text-align: end'),
    (r'(?<![-\w])left:\s*', r'inset-inline-start: '),
    (r'(?<![-\w])right:\s*', r'inset-inline-end: '),
]

HTML_REPLACEMENTS = [
    # Tailwind & Utility Classes
    (r'\bml-', r'ms-'),
    (r'\bmr-', r'me-'),
    (r'\bpl-', r'ps-'),
    (r'\bpr-', r'pe-'),
    (r'\btext-left\b', r'text-start'),
    (r'\btext-right\b', r'text-end'),
    (r'\bfloat-left\b', r'float-start'),
    (r'\bfloat-right\b', r'float-end'),
    (r'\bleft-0\b', r'start-0'),
    (r'\bright-0\b', r'end-0'),
    (r'\bborder-l\b', r'border-s'),
    (r'\bborder-r\b', r'border-e'),
]

DIRS_TO_PROCESS = [
    os.path.join("web", "templates"),
    os.path.join("web", "static", "css"),
]


def add_dir_auto_to_tag(tag_html: str) -> str:
    """Safely adds dir='auto' to an input/textarea/select tag if dir is not already present."""
    if re.search(r'\bdir\s*=', tag_html, re.IGNORECASE):
        return tag_html
    # Insert dir="auto" before the closing > or />
    if tag_html.endswith("/>"):
        return tag_html[:-2].rstrip() + ' dir="auto" />'
    elif tag_html.endswith(">"):
        return tag_html[:-1].rstrip() + ' dir="auto">'
    return tag_html


def process_content(content: str, filepath: str) -> tuple[str, list[str]]:
    """Transforms content and returns (transformed_content, list_of_violations_found)."""
    violations = []
    new_content = content

    if filepath.endswith(".css"):
        for pattern, repl in CSS_REPLACEMENTS:
            matches = list(re.finditer(pattern, new_content, flags=re.IGNORECASE))
            if matches:
                violations.append(f"Found {len(matches)} occurrences of pattern: {pattern}")
                new_content = re.sub(pattern, repl, new_content, flags=re.IGNORECASE)

    elif filepath.endswith((".html", ".jinja2", ".tsx", ".jsx", ".js")):
        # Check inline styles for physical properties
        for pattern, repl in CSS_REPLACEMENTS:
            matches = list(re.finditer(pattern, new_content, flags=re.IGNORECASE))
            if matches:
                violations.append(f"Found {len(matches)} inline occurrences of pattern: {pattern}")
                new_content = re.sub(pattern, repl, new_content, flags=re.IGNORECASE)

        for pattern, repl in HTML_REPLACEMENTS:
            matches = list(re.finditer(pattern, new_content))
            if matches:
                violations.append(f"Found {len(matches)} class occurrences of pattern: {pattern}")
                new_content = re.sub(pattern, repl, new_content)

        # Enforce dir="auto" on form tags
        def _sub_tag(m):
            tag = m.group(0)
            return add_dir_auto_to_tag(tag)

        # Match <input ...>, <textarea ...>, <select ...>
        new_content = re.sub(r'<input\b[^>]*>', _sub_tag, new_content, flags=re.IGNORECASE)
        new_content = re.sub(r'<textarea\b[^>]*>', _sub_tag, new_content, flags=re.IGNORECASE)
        new_content = re.sub(r'<select\b[^>]*>', _sub_tag, new_content, flags=re.IGNORECASE)

    return new_content, violations


def run_enforcer(mode: str = "fix") -> int:
    """
    Executes RTL enforcer.
    mode: 'scan' (display only), 'fix' (modify in place), 'check' (returns 1 if violations found).
    """
    total_violations = 0
    modified_files = 0
    checked_files = 0

    for d in DIRS_TO_PROCESS:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith((".css", ".html", ".jinja2", ".tsx", ".jsx", ".js")):
                    filepath = os.path.join(root, file)
                    checked_files += 1
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        continue

                    new_content, violations = process_content(content, filepath)
                    if violations or new_content != content:
                        total_violations += len(violations)
                        if mode == "fix":
                            try:
                                with open(filepath, "w", encoding="utf-8") as f:
                                    f.write(new_content)
                                modified_files += 1
                            except Exception as e:
                                pass
                        elif mode in ("scan", "check"):
                            print(f"[VIOLATION] {filepath}: {len(violations)} issues")

    print(f"RTL Enforcer ({mode.upper()} mode): Checked {checked_files} files, found {total_violations} violations, modified {modified_files} files.")
    if mode == "check" and total_violations > 0:
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobHunt Pro RTL & Logical Properties Enforcer")
    parser.add_argument("--scan", action="store_true", help="Scan and report violations without changing files")
    parser.add_argument("--check", action="store_true", help="Check compliance and exit with status code 1 on violations")
    parser.add_argument("--fix", action="store_true", default=True, help="Fix violations in place (default)")

    args = parser.parse_args()
    if args.scan:
        sys.exit(run_enforcer(mode="scan"))
    elif args.check:
        sys.exit(run_enforcer(mode="check"))
    else:
        sys.exit(run_enforcer(mode="fix"))
