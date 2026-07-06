#!/usr/bin/env python3
"""
QA Report Round 4 -- Secondary Pages Audit
Checks: title, h1, meta description, og:title, no physical CSS in <style> blocks.

PARTIAL TEMPLATES (no DOCTYPE / <html>): Only h1 is required.
FULL TEMPLATES: title + h1 + meta description + og:title all required.
"""
import os, re, json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "web" / "templates"

# These are partial templates injected into dashboard shell - they get title/meta from shell
PARTIAL_TEMPLATES = {
    "for_employers.html",
    "export.html",
    "stats.html",
    "funnel_analytics.html",
    "employer_track.html",
    "interview_prep.html",
    "new_campaign_v2.html",
    "offers.html",
}

TARGET_FILES = [
    "for_employers.html",
    "trust.html",
    "compare.html",
    "blog.html",
    "blog_post.html",
    "api_docs.html",
    "privacy.html",
    "terms.html",
    "forgot_password.html",
    "reset_password.html",
    "export.html",
    "stats.html",
    "chromeext.html",
    "offers.html",
    "checkout_v3.html",
    "funnel_analytics.html",
    "employer_track.html",
    "antigravity.html",
    "interview_prep.html",
    "new_campaign_v2.html",
]

PHYSICAL_CSS_PATTERN = re.compile(
    r'(?<![a-z-])(margin-left|margin-right|padding-left|padding-right)\s*:'
)

def extract_style_blocks(html):
    return "\n".join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE))

def check_file(filepath):
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"file": filepath.name, "error": str(e), "pass": False}

    style_content = extract_style_blocks(content)
    physical_matches = PHYSICAL_CSS_PATTERN.findall(style_content)

    is_partial = filepath.name in PARTIAL_TEMPLATES
    is_full = not is_partial

    has_title        = bool(re.search(r'<title[^>]*>[^<]{3,}</title>', content, re.IGNORECASE))
    has_h1           = bool(re.search(r'<h1[\s>]', content, re.IGNORECASE))
    has_description  = bool(re.search(r'<meta\s[^>]*name=["\']description["\']', content, re.IGNORECASE))
    has_og_title     = bool(re.search(r'<meta\s[^>]*property=["\']og:title["\']', content, re.IGNORECASE))
    no_physical_css  = len(physical_matches) == 0

    issues = []
    if not has_h1:           issues.append("MISSING <h1>")
    if not no_physical_css:  issues.append(f"PHYSICAL CSS found: {list(set(physical_matches))}")

    if is_full:
        if not has_title:       issues.append("MISSING <title>")
        if not has_description: issues.append("MISSING meta description")
        if not has_og_title:    issues.append("MISSING og:title")

    passed = len(issues) == 0

    result = {
        "file": filepath.name,
        "is_partial": is_partial,
        "pass": passed,
        "has_h1": has_h1,
        "no_physical_css": no_physical_css,
        "physical_css_violations": list(set(physical_matches)),
        "issues": issues,
    }
    if is_full:
        result.update({
            "has_title": has_title,
            "has_description": has_description,
            "has_og_title": has_og_title,
        })
    return result

def main():
    results = []
    for fname in TARGET_FILES:
        fpath = TEMPLATES_DIR / fname
        if not fpath.exists():
            results.append({"file": fname, "pass": False, "issues": ["FILE NOT FOUND"]})
            continue
        results.append(check_file(fpath))

    passed = [r for r in results if r.get("pass")]
    failed = [r for r in results if not r.get("pass")]

    report = {
        "summary": {
            "total": len(results),
            "passed": len(passed),
            "failed": len(failed),
        },
        "passed_files": [r["file"] for r in passed],
        "failed_files": [{"file": r["file"], "issues": r.get("issues", [])} for r in failed],
        "details": results,
    }

    output_path = Path(__file__).parent / "qa_report_round4.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print("  QA REPORT ROUND 4 -- SECONDARY PAGES")
    print("=" * 60)
    print(f"  Total:  {report['summary']['total']}")
    print(f"  [PASS]: {report['summary']['passed']}")
    print(f"  [FAIL]: {report['summary']['failed']}")
    print()

    if failed:
        print("FAILED FILES:")
        for f in failed:
            partial_tag = " [PARTIAL]" if results[[r["file"] for r in results].index(f["file"])].get("is_partial") else ""
            print(f"  [X] {f['file']}{partial_tag}")
            for issue in f.get("issues", []):
                print(f"      -> {issue}")
    else:
        print("  [OK] ALL FILES PASSED!")

    print()
    print(f"Full report -> qa_report_round4.json")
    print("=" * 60)

    return report

if __name__ == "__main__":
    main()
