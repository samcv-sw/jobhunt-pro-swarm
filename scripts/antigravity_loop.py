#!/usr/bin/env python
"""
Antigravity Optimization Loop & State Synthesizer
=================================================
Automates continuous project optimization by:
1. Parsing chat transcripts to synthesize state.
2. Executing workspace tests & diagnostic verification.
3. Automatically logging improvements and tracking token resources.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import UTC, datetime

logging.basicConfig(level=logging.DEBUG, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger("antigravity")

# Ensure stdout uses UTF-8 to prevent encoding errors on Windows terminal
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_WORKSPACE = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
DEFAULT_BRAIN_DIR = r"C:\Users\samde\.gemini\antigravity-ide\brain"
ALT_BRAIN_DIR = r"C:\Users\samde\.gemini\antigravity\brain"


def find_active_conversation_dir(brain_dir=None):
    """Dynamically finds the most recently updated conversation directory under candidate brain paths."""
    dirs_to_check = []
    if brain_dir:
        # If user explicitly specified a brain directory, only scan that directory
        dirs_to_check = [brain_dir]
    else:
        dirs_to_check = [DEFAULT_BRAIN_DIR, ALT_BRAIN_DIR, os.path.expanduser(r"~\\.gemini\\antigravity-ide\\brain"), os.path.expanduser(r"~\\.gemini\\antigravity\\brain")]

    # De-duplicate paths while preserving order
    unique_dirs = []
    for path in dirs_to_check:
        if path:
            norm_path = os.path.normpath(path)
            if norm_path not in unique_dirs:
                unique_dirs.append(norm_path)

    subdirs = []
    for b_dir in unique_dirs:
        if not os.path.exists(b_dir):
            continue
        for d in os.listdir(b_dir):
            full_path = os.path.join(b_dir, d)
            if os.path.isdir(full_path) and d != "scratch" and d != "tempmediaStorage":
                # Check if it has a transcript file
                transcript_file = os.path.join(full_path, ".system_generated", "logs", "transcript.jsonl")
                if os.path.exists(transcript_file):
                    mtime = os.path.getmtime(transcript_file)
                    subdirs.append((full_path, mtime, d))

    if not subdirs:
        return None

    # Sort by modification time descending
    subdirs.sort(key=lambda x: x[1], reverse=True)
    return subdirs[0][0]


def parse_transcript(transcript_path):
    """Parses a transcript.jsonl file into structured entries."""
    if not os.path.exists(transcript_path):
        return []

    entries = []
    with open(transcript_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def analyze_transcript(entries):
    """Synthesizes high-level statistics and tasks from transcript entries."""
    summary = {
        "user_requests": [],
        "completed_commands": [],
        "errors_encountered": [],
        "tested_files": set(),
        "modified_files": set(),
        "total_chars": 0,
        "step_count": len(entries)
    }

    # Regex patterns to detect errors in logs/outputs
    error_pattern = re.compile(r"(error|fail|exception|traceback|modulenotfounderror|filenotfounderror)", re.IGNORECASE)

    for entry in entries:
        content = entry.get("content", "")
        summary["total_chars"] += len(content)
        entry_type = entry.get("type")
        source = entry.get("source")

        if entry_type == "USER_INPUT":
            # Extract user request from content
            clean_content = content.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
            summary["user_requests"].append({
                "timestamp": entry.get("created_at"),
                "request": clean_content.split("\n")[0][:120]  # First line/summary
            })

        elif entry_type == "RUN_COMMAND":
            cmd = entry.get("command", "")
            summary["completed_commands"].append({
                "command": cmd,
                "status": entry.get("status")
            })

        # Check for tool call specifics
        if source == "MODEL" and entry_type == "PLANNER_RESPONSE":
            tool_calls = entry.get("tool_calls", [])
            for tc in tool_calls:
                args = tc.get("args", {})
                target_file = args.get("TargetFile") or args.get("AbsolutePath")
                if target_file:
                    file_name = os.path.basename(target_file)
                    if "test_" in file_name:
                        summary["tested_files"].add(file_name)
                    else:
                        summary["modified_files"].add(file_name)

        # Scan execution output for errors
        if entry_type in ["RUN_COMMAND", "VIEW_FILE", "LIST_DIRECTORY"] and entry.get("status") == "ERROR":
            summary["errors_encountered"].append({
                "type": entry_type,
                "error": content[:200]
            })

    return summary


def estimate_token_usage(total_chars):
    """Estimates the token count based on character length (approx 4 chars per token)."""
    return int(total_chars / 4)


def generate_state_report(workspace_path, conversation_dir):
    """Generates a beautiful ANTIGRAVITY_STATE_SUMMARY.md file in the workspace root."""
    if not conversation_dir:
        logger.debug("[-] Active conversation directory not found. Cannot parse transcript.")
        return False

    conv_id = os.path.basename(conversation_dir)
    transcript_path = os.path.join(conversation_dir, ".system_generated", "logs", "transcript.jsonl")

    logger.debug(f"[*] Parsing transcript logs from: {transcript_path}")
    entries = parse_transcript(transcript_path)
    if not entries:
        logger.debug("[-] Transcript file is empty or missing.")
        return False

    stats = analyze_transcript(entries)
    estimated_tokens = estimate_token_usage(stats["total_chars"])
    token_limit = 2000000  # Default model context window limit
    token_percentage = (estimated_tokens / token_limit) * 100

    report_path = os.path.join(workspace_path, "ANTIGRAVITY_STATE_SUMMARY.md")

    # Read git status
    git_status = "Unknown"
    try:
        git_status = subprocess.check_output(["git", "status", "-s"], cwd=workspace_path, text=True)
    except Exception:
        pass

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Antigravity Optimization Loop — State Summary\n\n")
        f.write(f"> Generated on {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')} | Conv ID: `{conv_id}`\n\n")

        f.write("## 📊 Context & Token Usage\n")
        f.write(f"- **Steps Completed**: {stats['step_count']}\n")
        f.write(f"- **Total Transcript Size**: {stats['total_chars'] / 1024:.2f} KB\n")
        f.write(f"- **Estimated Token Usage**: {estimated_tokens:,} tokens (~{token_percentage:.2f}% of 2M limit)\n")
        if token_percentage > 85:
            f.write("  > [!WARNING]\n  > Token usage is extremely high. Consider committing changes and starting a fresh session.\n\n")
        else:
            f.write("  > [!NOTE]\n  > Token resources are healthy. Safe to continue iterative changes.\n\n")

        f.write("## 🎯 Active User Objectives\n")
        for req in stats["user_requests"][-5:]:
            f.write(f"- `[{req['timestamp']}]` {req['request']}\n")
        f.write("\n")

        f.write("## 📂 Workspace Changes Tracked\n")
        f.write(f"### Git Dirty State:\n```text\n{git_status or 'Clean (No unstaged changes)'}\n```\n\n")

        f.write("### Code Modifications Analyzed:\n")
        for f_name in sorted(list(stats["modified_files"])):
            f.write(f"- `{f_name}`\n")
        if not stats["modified_files"]:
            f.write("- None detected in transcript\n")
        f.write("\n")

        f.write("## 🧪 Tests & Verification\n")
        for t_file in sorted(list(stats["tested_files"])):
            f.write(f"- `{t_file}`\n")
        if not stats["tested_files"]:
            f.write("- No tests verified in transcript\n")
        f.write("\n")

        if stats["errors_encountered"]:
            f.write("## ⚠️ Logged Execution Issues\n")
            for err in stats["errors_encountered"][-5:]:
                f.write(f"- **Type**: `{err['type']}` | {err['error']}\n")
            f.write("\n")

    logger.debug(f"[+] State report successfully synthesized: {report_path}")
    return True


def run_workspace_tests(workspace_path):
    """Executes pytest suite on the tests/ directory and prints summary."""
    logger.debug("[*] Launching project verification tests...")
    try:
        res = subprocess.run(["pytest", "tests/"], cwd=workspace_path, capture_output=True, text=True)
        logger.debug(res.stdout)
        if res.returncode == 0:
            logger.debug("[+] All verification tests passed successfully!")
            return True
        else:
            logger.debug("[-] Test suite encountered failures. Please review stdout.")
            return False
    except FileNotFoundError:
        logger.debug("[-] Pytest executable not found in PATH.")
        return False


def run_workspace_cleanup(workspace_path):
    """Triggers workspace temp/cache cleaning."""
    cleanup_script = os.path.join(workspace_path, "cleanup_temp.py")
    if os.path.exists(cleanup_script):
        logger.debug(f"[*] Running workspace cleaner: {cleanup_script}")
        res = subprocess.run([sys.executable, cleanup_script], cwd=workspace_path, capture_output=True, text=True)
        logger.debug(res.stdout)
        return True
    else:
        logger.debug("[-] cleanup_temp.py script not found in workspace.")
        return False


def log_new_improvement(workspace_path, summary_text, conv_id):
    """Appends a new logged improvement to .antigravity_improvements.json."""
    log_path = os.path.join(workspace_path, ".antigravity_improvements.json")

    # Auto-detect modified files via git if summary_text is default
    if not summary_text or summary_text == "auto":
        try:
            modified = subprocess.check_output(["git", "diff", "--name-only"], cwd=workspace_path, text=True).strip()
            if modified:
                files = [f.strip() for f in modified.split("\n") if f.strip()]
                summary_text = f"Optimized workspace files: {', '.join(files[:4])}"
            else:
                summary_text = "Performed workspace configuration audit"
        except Exception:
            summary_text = "Executed iterative workspace optimization"

    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary_text,
        "conversation_id": conv_id or "unspecified"
    }

    data = []
    if os.path.exists(log_path):
        try:
            with open(log_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []

    data.append(new_entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.debug("[+] Successfully logged improvement to `.antigravity_improvements.json`:")
    logger.debug(f"    - Summary: '{summary_text}'")
    logger.debug(f"    - Conv ID: {conv_id}")
    return True


def check_workspace_health(workspace_path):
    """Performs quick validation of the project's setup."""
    logger.debug("==================================================")
    logger.debug("   JOBHUNT PRO / ANTIGRAVITY WORKSPACE HEALTH")
    logger.debug("==================================================")

    # Check DB shim — it lives in web/app_v2.py, not config.py
    app_v2_path = os.path.join(workspace_path, "web", "app_v2.py")
    if os.path.exists(app_v2_path):
        with open(app_v2_path, encoding="utf-8") as f:
            content = f.read()
            if "pg_sqlite_shim" in content:
                logger.debug("[OK] SQLite database shim imported in web/app_v2.py")
            else:
                logger.debug("[WARN] pg_sqlite_shim not found in web/app_v2.py")
    else:
        logger.debug("[WARN] web/app_v2.py is missing!")

    # Check .clinerules rules file
    clinerules_path = os.path.join(workspace_path, ".clinerules")
    if os.path.exists(clinerules_path):
        size_kb = os.path.getsize(clinerules_path) // 1024
        logger.debug(f"[OK] .clinerules loaded ({size_kb} KB)")
    else:
        logger.debug("[WARN] .clinerules not found — run 'loop' to bootstrap rules")

    # Check env credentials template
    env_file = os.path.join(workspace_path, ".env")
    if os.path.exists(env_file):
        logger.debug("[OK] .env configuration file exists locally")
    else:
        logger.debug("[WARN] .env configuration file is missing (using defaults or environment variables)")

    # Check tests directory
    tests_dir = os.path.join(workspace_path, "tests")
    if os.path.exists(tests_dir):
        test_count = len([f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")])
        logger.debug(f"[OK] tests/ directory found — {test_count} test modules")
    else:
        logger.debug("[WARN] tests/ directory missing — no automated tests")

    # Run DB connection check
    check_db_script = os.path.join(workspace_path, "check_tables.py")
    if os.path.exists(check_db_script):
        res = subprocess.run([sys.executable, check_db_script], cwd=workspace_path, capture_output=True, text=True)
        if res.returncode == 0:
            logger.debug("[OK] Database connection and schema validated successfully")
        else:
            logger.debug(f"[WARN] DB Schema validation script exited with code {res.returncode}")


    logger.debug("==================================================")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Optimization Loop Command Center")
    parser.add_argument("command", choices=["summary", "test", "cleanup", "log-improvement", "check", "loop"],
                        help="The operation command to execute")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="Absolute path to the workspace")
    parser.add_argument("--brain", default=None, help="Path to local brain transcripts folder")
    parser.add_argument("--summary", dest="summary_text", default="auto", help="Summary text for logging improvements")

    args = parser.parse_args()

    workspace_path = args.workspace
    brain_dir = args.brain

    if not os.path.exists(workspace_path):
        logger.debug(f"[-] Workspace path does not exist: {workspace_path}")
        sys.exit(1)

    # Resolve active conversation
    conv_dir = find_active_conversation_dir(brain_dir)
    conv_id = os.path.basename(conv_dir) if conv_dir else None

    if args.command == "summary":
        success = generate_state_report(workspace_path, conv_dir)
        sys.exit(0 if success else 1)

    elif args.command == "test":
        success = run_workspace_tests(workspace_path)
        sys.exit(0 if success else 1)

    elif args.command == "cleanup":
        success = run_workspace_cleanup(workspace_path)
        sys.exit(0 if success else 1)

    elif args.command == "log-improvement":
        success = log_new_improvement(workspace_path, args.summary_text, conv_id)
        sys.exit(0 if success else 1)

    elif args.command == "check":
        check_workspace_health(workspace_path)
        sys.exit(0)

    elif args.command == "loop":
        logger.debug("[*] Starting Antigravity continuous feedback loop...")
        run_workspace_cleanup(workspace_path)
        run_workspace_tests(workspace_path)
        generate_state_report(workspace_path, conv_dir)
        logger.debug("[+] Loop step complete. Workspace is ready for further edits.")
        sys.exit(0)


if __name__ == "__main__":
    main()
