"""
JobHunt Pro - Auto Improvement Loop v3.0 (ADVANCED)
=====================================================
Phase 7, Task 7.1 — Full implementation with:
  1. Read ALL project files (not just monitored ones)
  2. Analyze chat transcripts for improvement suggestions
  3. Generate improvement requests with specific code changes
  4. Track which files have been improved and when
  5. Prioritize improvements by impact (high/medium/low)

Zero investment, permanent cloud operation, 24/7 self-improvement.
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger("auto_improve")

PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_DIRS = [
    Path.home() / ".gemini" / "antigravity" / "brain",
    Path.home() / ".gemini" / "antigravity-ide" / "brain",
]
STATE_FILE = PROJECT_ROOT / ".auto_improve_state.json"
IMPROVE_ME_FILE = PROJECT_ROOT / "docs" / "IMPROVE_ME.md"

# ── Impact Levels ──────────────────────────────────────────────────────────────

IMPACT_LEVELS = {
    "critical": {"weight": 10, "label": "[CRITICAL]", "desc": "Security, data loss, crash fixes"},
    "high":    {"weight": 7,  "label": "[HIGH]",     "desc": "Major features, performance, scalability"},
    "medium":  {"weight": 4,  "label": "[MEDIUM]",   "desc": "Enhancements, new integrations, optimization"},
    "low":     {"weight": 1,  "label": "[LOW]",      "desc": "Docs, minor tweaks, code cleanup"},
}

# ── File categories for analysis ──────────────────────────────────────────────

CATEGORY_PATTERNS = {
    "core_engine":    [r"core/", r"orchestrator\.py", r"config\.py"],
    "web_api":        [r"web/", r"api/", r"templates/"],
    "scrapers":       [r"scraper", r"collector", r"job_search"],
    "ai_ml":          [r"ai_", r"llm_", r"tailor", r"predictor", r"personalizer"],
    "email":          [r"email", r"smtp", r"mail"],
    "security":       [r"ban_", r"anti_", r"stealth", r"shield", r"captcha"],
    "deployment":     [r"deploy", r"Docker", r"docker", r"render", r"cloud", r"k8s", r"infra"],
    "scripts_tools":  [r"scripts/", r"auto_", r"check_", r"run_", r"start_"],
    "data_db":        [r"database", r"sqlite", r"pg_", r"db_", r"migrate"],
    "docs_config":    [r"\.md$", r"\.json$", r"\.yml$", r"\.yaml$", r"\.toml$", r"\.env", r"\.ini"],
}

# ── Excluded patterns (noise reduction) ──────────────────────────────────────

EXCLUDE_PATTERNS = [
    r"\.venv",
    r"__pycache__",
    r"\.git",
    r"\.pytest_cache",
    r"node_modules",
    r"\.wrangler",
    r"\.agents",
    r"sent_mails/",
    r"downloaded_cvs/",
    r"kronos_exports/",
    r"screenshots/",
    r"proxy_test_results/",
    r"test_env",
    r"_backups/",
    r"archive/",
    r"templates_backup/",
    r"\.db$",
    r"\.sqlite3?$",
    r"\.pyc$",
    r"\.log$",
    r"\.exe$",
    r"\.zip$",
    r"\.lnk$",
]

def is_production_runtime_code(rel_path: str) -> bool:
    """Check if the file is production runtime code (versus tests, models, schemas, or one-off scripts)."""
    path_lower = rel_path.lower().replace("\\", "/")
    if "test" in path_lower or "scripts/" in path_lower or "models.py" in path_lower:
        return False
    return True

def detect_missing_error_handling(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect files missing try/except blocks."""
    if not is_production_runtime_code(rel_path):
        return 0, []
    score = 0
    reasons = []
    if content.count("try:") < 2 and len(content) > 5000:
        score += 3
        reasons.append("Missing error handling (few try/except blocks for size)")
    if "except" not in content and len(content) > 2000:
        score += 2
        reasons.append("No exception handling at all")
    return score, reasons

def detect_missing_logging(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect files missing logging setup."""
    if not is_production_runtime_code(rel_path):
        return 0, []
    score = 0
    reasons = []
    if "logging" not in content and len(content) > 3000:
        score += 2
        reasons.append("No logging configured")
    if "logger." not in content and len(content) > 2000:
        score += 1
        reasons.append("No logger usage detected")
    return score, reasons

def detect_missing_type_hints(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect Python files missing type hints."""
    score = 0
    reasons = []
    if rel_path.endswith(".py") and len(content) > 2000:
        # Find all function definitions in the file
        funcs = re.findall(r'def\s+\w+\s*\(', content)
        if len(funcs) > 5:
            # A function is considered typed if it has a colon inside params, or -> return type hint
            typed_count = 0
            matches = list(re.finditer(r'def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^\n:]+))?\s*:', content, re.DOTALL))
            for m in matches:
                params = m.group(2)
                return_hint = m.group(3)
                if return_hint or (":" in params):
                    typed_count += 1

            total_parsed = len(matches)
            total_funcs = max(len(funcs), total_parsed)
            if total_funcs > 5 and typed_count < total_funcs * 0.3:
                score += 2
                reasons.append(f"Missing type hints ({typed_count}/{total_funcs} functions typed)")
    return score, reasons

def detect_missing_docstrings(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect Python files missing docstrings."""
    score = 0
    reasons = []
    if rel_path.endswith(".py") and len(content) > 2000:
        classes = re.findall(r'class \w+', content)
        funcs = re.findall(r'def \w+\(', content)
        docstrings = content.count('"""') // 2
        total_defs = len(classes) + len(funcs)
        if total_defs > 5 and docstrings < total_defs * 0.3:
            score += 2
            reasons.append(f"Missing docstrings ({docstrings}/{total_defs} definitions documented)")
    return score, reasons

def detect_small_underdeveloped(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect files that are suspiciously small for their purpose."""
    score = 0
    reasons = []
    size_kb = len(content) / 1024
    if size_kb < 3 and rel_path.endswith(".py") and "core/" in rel_path:
        score += 4
        reasons.append(f"Underdeveloped core file (only {size_kb:.1f}KB)")
    return score, reasons

def detect_stale_files(content: str, rel_path: str, mtime: float) -> tuple[int, list[str]]:
    """Detect files not modified recently."""
    score = 0
    reasons = []
    now = datetime.now().timestamp()
    days_old = (now - mtime) / 86400
    if days_old > 14 and rel_path.endswith(".py") and "core/" in rel_path:
        score += min(int(days_old / 7), 5)
        reasons.append(f"Not modified in {int(days_old)} days")
    return score, reasons

def detect_complexity_issues(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect overly complex functions/methods."""
    score = 0
    reasons = []
    if rel_path.endswith(".py"):
        # Rough complexity: count long functions
        lines = content.split("\n")
        current_func = None
        func_lines = 0
        for i, line in enumerate(lines):
            if re.match(r'^\s*def \w+\(', line) or re.match(r'^\s*async def \w+\(', line):
                if current_func and func_lines > 80:
                    score += 1
                    reasons.append(f"Long function '{current_func}' ({func_lines} lines)")
                current_func = re.search(r'def (\w+)', line)
                current_func = current_func.group(1) if current_func else "unknown"
                func_lines = 0
            elif current_func:
                if line.strip() and not line.strip().startswith("#"):
                    # Column 0 lines mean top-level scope returned, so function ended
                    if line and not line[0].isspace() and not line.startswith('@'):
                        current_func = None
                        func_lines = 0
                        continue
                    func_lines += 1
        if current_func and func_lines > 80:
            score += 1
            reasons.append(f"Long function '{current_func}' ({func_lines} lines)")
    return score, reasons

def detect_hardcoded_config(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect hardcoded values that should be in config."""
    score = 0
    reasons = []
    if rel_path.endswith(".py") and "config.py" not in rel_path:
        # Detect hardcoded URLs, API keys patterns
        hardcoded_urls = len(re.findall(r'https?://[^\s"\'\)]+', content))
        if hardcoded_urls > 3:
            score += 2
            reasons.append(f"Hardcoded URLs ({hardcoded_urls} found, should use config)")
    return score, reasons

def detect_missing_tests(content: str, rel_path: str) -> tuple[int, list[str]]:
    """Detect core files without corresponding test files."""
    score = 0
    reasons = []
    if rel_path.endswith(".py") and "core/" in rel_path:
        basename = os.path.basename(rel_path)
        test_file = PROJECT_ROOT / "tests" / f"test_{basename}"
        if not test_file.exists():
            score += 2
            reasons.append("No corresponding test file")
    return score, reasons


# ── All detectors ─────────────────────────────────────────────────────────────

ALL_DETECTORS = [
    detect_missing_error_handling,
    detect_missing_logging,
    detect_missing_type_hints,
    detect_missing_docstrings,
    detect_small_underdeveloped,
    detect_stale_files,
    detect_complexity_issues,
    detect_hardcoded_config,
    detect_missing_tests,
]


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_file_hash(path):
    """Get MD5 hash of a file."""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def get_file_size(path):
    """Get file size in KB."""
    try:
        return os.path.getsize(path) / 1024
    except Exception:
        return 0

def get_file_mtime(path):
    """Get file modification time as ISO string."""
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
    except Exception:
        return "unknown"

def get_file_mtime_ts(path):
    """Get file modification time as timestamp."""
    try:
        return os.path.getmtime(path)
    except Exception:
        return 0

def read_file_safe(path, max_lines=200):
    """Read first N lines of a file safely."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return "".join(lines[:max_lines]), len(lines)
    except Exception:
        return "", 0

def read_entire_file_safe(path):
    """Read entire file safely."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def should_exclude(rel_path):
    """Check if a path should be excluded from analysis."""
    normalized_path = str(rel_path).replace("\\", "/")
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, normalized_path):
            return True
    return False

def categorize_file(rel_path):
    """Categorize a file based on its path."""
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, str(rel_path)):
                return category
    return "other"

def get_all_project_files():
    """Get ALL project files recursively, excluding noise."""
    all_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT)
            if should_exclude(rel_path):
                continue
            # Only include relevant file types
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.py', '.html', '.js', '.css', '.md', '.json', '.yml', '.yaml',
                       '.toml', '.ini', '.cfg', '.txt', '.sh', '.bat', '.ps1', '.sql',
                       '.env', '.dockerfile', '.conf', '.xml', '.svg'] or \
               f.endswith('.env') or f.endswith('.dockerfile') or \
               f in ['Dockerfile', 'Procfile', 'Caddyfile', 'nginx.conf']:
                all_files.append({
                    "path": full_path,
                    "rel_path": rel_path,
                    "ext": ext,
                    "size_kb": round(get_file_size(full_path), 1),
                    "mtime": get_file_mtime(full_path),
                    "mtime_ts": get_file_mtime_ts(full_path),
                    "hash": get_file_hash(full_path)[:8],
                    "category": categorize_file(rel_path),
                })
    return all_files

def get_transcript_summary(path):
    """Get summary of a transcript file."""
    try:
        size_kb = os.path.getsize(path) / 1024
        with open(path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = content.split("\n")
        # Extract user messages (Arabic or English)
        user_msgs = []
        for line in lines:
            line_lower = line.lower()
            if any(x in line_lower for x in ["bade", "dear", "ana", "wanted", "need", "please",
                                              "make", "add", "fix", "improve", "create", "update",
                                              "change", "implement", "remove", "delete", "build",
                                              "write", "modify", "refactor", "optimize"]):
                if len(line) > 20 and len(line) < 500:
                    user_msgs.append(line.strip()[:200])
        return {
            "size_kb": round(size_kb, 1),
            "total_lines": len(lines),
            "user_requests": user_msgs[:15],
            "hash": hashlib.md5(content.encode()).hexdigest()[:12],
            "path": str(path),
        }
    except Exception:
        return {"size_kb": 0, "total_lines": 0, "user_requests": [], "hash": "", "path": ""}

def analyze_file_for_improvements(file_info):
    """Run all detectors on a file and return improvement opportunities."""
    content = read_entire_file_safe(file_info["path"])
    if not content:
        return []

    opportunities = []
    total_score = 0

    for detector in ALL_DETECTORS:
        try:
            score, reasons = detector(content, file_info["rel_path"])
            if score > 0:
                total_score += score
                for reason in reasons:
                    opportunities.append({
                        "file": file_info["rel_path"],
                        "issue": reason,
                        "score": score,
                        "category": file_info["category"],
                        "size_kb": file_info["size_kb"],
                    })
        except Exception:
            pass

    return opportunities

def prioritize_opportunities(opportunities):
    """Prioritize improvement opportunities by impact score."""
    # Group by file
    by_file = defaultdict(list)
    for opp in opportunities:
        by_file[opp["file"]].append(opp)

    # Calculate total score per file
    file_scores = []
    for file_path, opps in by_file.items():
        total = sum(o["score"] for o in opps)
        avg = total / len(opps)
        file_scores.append({
            "file": file_path,
            "total_score": total,
            "avg_score": round(avg, 1),
            "issue_count": len(opps),
            "issues": [o["issue"] for o in opps],
            "category": opps[0]["category"],
            "size_kb": opps[0]["size_kb"],
        })

    # Sort by total score descending
    file_scores.sort(key=lambda x: (-x["total_score"], -x["issue_count"]))

    # Assign impact levels
    for fs in file_scores:
        if fs["total_score"] >= 8:
            fs["impact"] = "critical"
        elif fs["total_score"] >= 5:
            fs["impact"] = "high"
        elif fs["total_score"] >= 3:
            fs["impact"] = "medium"
        else:
            fs["impact"] = "low"

    return file_scores

def load_state():
    """Load the auto-improvement state from JSON."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "iteration": 0,
        "last_improvement_time": None,
        "improvements_made": [],
        "files_modified": {},
        "total_improvements": 0,
        "started_at": datetime.now(UTC).isoformat(),
        "files_analyzed_count": 0,
        "opportunities_found": 0,
        "opportunities_completed": 0,
    }

def save_state(state):
    """Save the auto-improvement state to JSON."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

def generate_improvement_request(file_score, state):
    """Generate a detailed improvement request file for a specific file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_score["file"])
    req_file = PROJECT_ROOT / ".agents" / "improve_requests" / f"_improve_request_{timestamp}_{sanitized_name}.md"
    os.makedirs(req_file.parent, exist_ok=True)

    # Read current file content
    full_path = PROJECT_ROOT / file_score["file"]
    content, total_lines = read_file_safe(full_path, max_lines=300)

    impact_info = IMPACT_LEVELS.get(file_score["impact"], IMPACT_LEVELS["medium"])

    lines = []
    lines.append("# Auto Improvement Request")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append(f"**Iteration:** {state['iteration'] + 1}")
    lines.append(f"**Priority:** {impact_info['label']} (score: {file_score['total_score']})")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## TARGET FILE")
    lines.append("")
    lines.append(f"- **File:** `{file_score['file']}`")
    lines.append(f"- **Category:** {file_score['category']}")
    lines.append(f"- **Size:** {file_score['size_kb']}KB")
    lines.append(f"- **Issues detected ({file_score['issue_count']}):**")
    for issue in file_score['issues']:
        lines.append(f"  - {issue}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Current Content (first {min(total_lines, 300)} lines)")
    lines.append("")
    lines.append("```python")
    lines.append(content)
    if total_lines > 300:
        lines.append(f"# ... ({total_lines - 300} more lines)")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Improvement Tasks")
    lines.append("")
    for i, issue in enumerate(file_score['issues'], 1):
        lines.append(f"{i}. **{issue}**")
    lines.append("")
    lines.append("### Suggested Improvements:")
    lines.append("")
    lines.append("1. Add proper error handling (try/except blocks)")
    lines.append("2. Add logging configuration and usage")
    lines.append("3. Add type hints to all function signatures")
    lines.append("4. Add docstrings to all classes and functions")
    lines.append("5. Extract hardcoded values to config.py")
    lines.append("6. Break down long functions into smaller ones")
    lines.append("7. Add comprehensive tests")
    lines.append("8. Optimize performance (caching, async, etc.)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("After completing, delete this file and update the state file.")
    lines.append("")

    with open(req_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return req_file.name

def build_master_context(all_files, opportunities, state, transcripts):
    """Build the master context file — IMPROVE_ME.md (enhanced version)."""

    lines = []
    lines.append("# 🚀 JobHunt Pro — Master Improvement Context v3.0")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append(f"**Iteration:** {state['iteration'] + 1}")
    lines.append(f"**Total improvements made:** {state['total_improvements']}")
    lines.append(f"**Files analyzed:** {len(all_files)}")
    lines.append(f"**Opportunities found:** {len(opportunities)}")
    lines.append("**Goal:** Read this file, understand everything, then improve the project to maximum.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📋 Instructions for the AI")
    lines.append("")
    lines.append("1. Read this entire file carefully")
    lines.append("2. Read the project files listed below")
    lines.append("3. Read the chat transcripts listed below")
    lines.append("4. Identify what can be improved")
    lines.append("5. Make ALL improvements you can")
    lines.append("6. When done, update this file's 'Last Improvement' section")
    lines.append("7. Keep improving until you run out of tokens")
    lines.append("")
    lines.append("**Constraints:**")
    lines.append("- Everything must be $0 (zero investment)")
    lines.append("- Everything must run on cloud (nothing on PC)")
    lines.append("- Must work 24/7 permanently")
    lines.append("- Must scale to 1M+ users")
    lines.append("- Must have 0% ban risk")
    lines.append("- Use tricks from China, USA, Russia, worldwide")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 Project State")
    lines.append("")

    # ── File status by category ──
    by_category = defaultdict(list)
    for f in all_files:
        by_category[f["category"]].append(f)

    for cat in ["core_engine", "web_api", "scrapers", "ai_ml", "email", "security",
                 "deployment", "scripts_tools", "data_db", "docs_config", "other"]:
        cat_files = by_category.get(cat, [])
        if not cat_files:
            continue
        cat_label = cat.replace("_", " ").title()
        lines.append(f"### {cat_label} ({len(cat_files)} files)")
        lines.append("")
        lines.append("| File | Size | Modified | Hash |")
        lines.append("|------|------|----------|------|")
        for f in sorted(cat_files, key=lambda x: x["rel_path"]):
            lines.append(f"| [`{f['rel_path']}`]({f['rel_path']}) | {f['size_kb']}KB | {f['mtime']} | `{f['hash']}` |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 🔄 Improvement History")
    lines.append("")

    improvements = state.get("improvements_made", [])
    lines.append(f"**Total improvements made so far:** {len(improvements)}")
    lines.append("")
    if improvements:
        for i, imp in enumerate(improvements[-30:], 1):
            ts = imp.get('timestamp', 'unknown')
            desc = imp.get('description', 'unknown')
            impact = imp.get('impact', 'unknown')
            files_mod = imp.get('files_modified', [])
            files_str = ", ".join(files_mod[:5])
            if len(files_mod) > 5:
                files_str += f" +{len(files_mod)-5} more"
            lines.append(f"{i}. **{ts}** [{impact}] — {desc}")
            lines.append(f"   Files: {files_str}")
    else:
        lines.append("No improvements recorded yet. This is the first run.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 💡 Improvement Opportunities (Prioritized)")
    lines.append("")

    if opportunities:
        # Group by impact
        by_impact = defaultdict(list)
        for opp in opportunities:
            by_impact[opp["impact"]].append(opp)

        for impact_level in ["critical", "high", "medium", "low"]:
            impact_opps = by_impact.get(impact_level, [])
            if not impact_opps:
                continue
            impact_info = IMPACT_LEVELS[impact_level]
            lines.append(f"### {impact_info['label']} ({len(impact_opps)} items)")
            lines.append("")
            lines.append("| # | File | Issues | Score | Size |")
            lines.append("|---|------|--------|-------|------|")
            for i, opp in enumerate(impact_opps[:15], 1):
                issues_short = opp['issues'][0][:60] + "..." if len(opp['issues'][0]) > 60 else opp['issues'][0]
                extra = f"+{len(opp['issues'])-1} more" if len(opp['issues']) > 1 else ""
                lines.append(f"| {i} | [`{opp['file']}`]({opp['file']}) | {issues_short} {extra} | {opp['total_score']} | {opp['size_kb']}KB |")
            if len(impact_opps) > 15:
                lines.append("| ... | ... | ... | ... | ... |")
            lines.append("")
    else:
        lines.append("No improvement opportunities detected. The project is in great shape!")
        lines.append("")

    lines.append("### General Improvement Ideas")
    lines.append("")
    lines.append("- Add more job titles to search queries")
    lines.append("- Add more locations to worldwide search")
    lines.append("- Enhance AI prompts for better cover letters")
    lines.append("- Add more SMTP providers to rotation")
    lines.append("- Improve anti-ban detection patterns")
    lines.append("- Add more curated contacts per country")
    lines.append("- Enhance ATS keyword matching")
    lines.append("- Add more email templates")
    lines.append("- Improve rate limiting algorithms")
    lines.append("- Add more monitoring and alerting")
    lines.append("- Optimize database queries")
    lines.append("- Add more caching")
    lines.append("- Improve error handling")
    lines.append("- Add more unit tests")
    lines.append("- Enhance documentation")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📝 Recent Chat Transcripts")
    lines.append("")

    lines.append(f"**Found {len(transcripts)} transcripts in brain directories**")
    lines.append("")

    if transcripts:
        for t in transcripts[:20]:
            lines.append(f"### `{t['name']}`")
            lines.append(f"- Size: {t['size_kb']}KB, Lines: {t['total_lines']}, Hash: `{t['hash']}`")
            if t['user_requests']:
                lines.append("- Key requests:")
                for req in t['user_requests'][:5]:
                    lines.append(f"  - \"{req}\"")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## ✅ Last Improvement")
    lines.append("")
    lines.append("**This section should be updated by the AI after making improvements.**")
    lines.append("")
    lines.append(f"- Timestamp: {datetime.now().isoformat()}")
    lines.append("- Files modified: (list here)")
    lines.append("- Changes made: (describe here)")
    lines.append("- Next focus: (what to improve next)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🚀 Quick Start for Next Chat")
    lines.append("")
    lines.append("1. Read this file: `IMPROVE_ME.md`")
    lines.append("2. Read the project files listed above")
    lines.append("3. Read the chat transcripts listed above")
    lines.append("4. Make improvements")
    lines.append("5. Update the 'Last Improvement' section above")
    lines.append("6. Repeat until tokens run out")
    lines.append("")

    return "\n".join(lines)


def main():
    logger.debug("=" * 70)
    logger.debug("  JobHunt Pro — Auto Improvement Loop v3.0 (ADVANCED)")
    logger.debug("  Phase 7, Task 7.1 — Full Implementation")
    logger.debug("=" * 70)
    logger.debug("")

    start_time = time.time()

    # ── Step 1: Load state ──
    logger.debug("[1/7] Loading improvement state...")
    state = load_state()
    state["iteration"] += 1
    logger.debug(f"  -> Iteration #{state['iteration']}")
    logger.debug(f"  -> Total improvements so far: {state['total_improvements']}")

    # ── Step 2: Scan ALL project files ──
    logger.debug("\n[2/7] Scanning ALL project files...")
    all_files = get_all_project_files()
    logger.debug(f"  -> Found {len(all_files)} analyzable files")

    # Count by category
    by_category = defaultdict(int)
    for f in all_files:
        by_category[f["category"]] += 1
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        logger.debug(f"     {cat.replace('_', ' ').title()}: {count}")

    state["files_analyzed_count"] = len(all_files)

    # ── Step 3: Analyze files for improvements ──
    logger.debug("\n[3/7] Analyzing files for improvement opportunities...")
    all_opportunities = []
    for f in all_files:
        if f["ext"] == ".py":  # Only analyze Python files deeply
            opps = analyze_file_for_improvements(f)
            all_opportunities.extend(opps)

    logger.debug(f"  -> Found {len(all_opportunities)} raw improvement signals")

    # ── Step 4: Prioritize opportunities ──
    logger.debug("\n[4/7] Prioritizing improvement opportunities...")
    prioritized = prioritize_opportunities(all_opportunities)
    logger.debug(f"  -> {len(prioritized)} files with improvement potential")

    # Count by impact
    by_impact = defaultdict(int)
    for p in prioritized:
        by_impact[p["impact"]] += 1
    for impact in ["critical", "high", "medium", "low"]:
        if by_impact[impact] > 0:
            info = IMPACT_LEVELS[impact]
            logger.debug(f"     {info['label']}: {by_impact[impact]} files")

    state["opportunities_found"] = len(prioritized)

    # ── Step 5: Generate improvement requests for top priorities ──
    logger.debug("\n[5/7] Generating improvement requests...")
    requests_generated = 0
    for opp in prioritized[:5]:  # Top 5 priorities
        if opp["impact"] in ["critical", "high"]:
            req_name = generate_improvement_request(opp, state)
            logger.debug(f"  -> Created: {req_name} ({opp['impact']})")
            requests_generated += 1

    if requests_generated == 0:
        logger.debug("  -> No high-priority improvement requests needed")

    # ── Step 6: Find and analyze chat transcripts ──
    logger.debug("\n[6/7] Analyzing chat transcripts...")
    all_transcripts = []
    for brain_dir in BRAIN_DIRS:
        if brain_dir.exists():
            for f in brain_dir.iterdir():
                if f.is_file() and f.suffix == "":
                    all_transcripts.append(f)

    # Sort by modification time (newest first)
    all_transcripts.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    transcript_data = []
    for t in all_transcripts[:30]:
        summary = get_transcript_summary(t)
        if summary["size_kb"] > 0:
            transcript_data.append({
                "name": t.name,
                **summary
            })

    logger.debug(f"  -> Found {len(all_transcripts)} transcripts")
    logger.debug(f"  -> Analyzed {len(transcript_data)} with content")

    # ── Step 7: Build master context ──
    logger.debug("\n[7/7] Building master context...")
    context = build_master_context(all_files, prioritized, state, transcript_data)

    with open(IMPROVE_ME_FILE, "w", encoding="utf-8") as f:
        f.write(context)

    size_kb = round(os.path.getsize(IMPROVE_ME_FILE) / 1024, 1)
    logger.debug(f"  -> Written to IMPROVE_ME.md ({size_kb}KB)")

    # Save state
    save_state(state)

    elapsed = time.time() - start_time
    logger.debug("")
    logger.debug("=" * 70)
    logger.debug(f"  DONE! ({elapsed:.1f}s)")
    logger.debug("")
    logger.debug("  Now open a NEW chat in Roo Code and say:")
    logger.debug("")
    logger.debug('    "2ri IMPROVE_ME.md w3mel li maktoub"')
    logger.debug("")
    logger.debug("  The AI will read everything and continue improving.")
    logger.debug("=" * 70)


if __name__ == "__main__":
    main()
