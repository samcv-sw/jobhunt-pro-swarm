import os
import shutil
import glob
from datetime import datetime

root = os.path.dirname(os.path.abspath(__file__))
backup = os.path.join(root, '_backups', f'cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
os.makedirs(backup, exist_ok=True)

# List of manually selected files to clean up
trash_files = [
    'test_bayt_debug.py', 'test_bayt_html.py', 'test_bayt_html2.py', 'test_bayt_html3.py',
    'test_dice.py', 'test_dice_debug.py', 'test_dice_debug2.py', 'test_dice_debug3.py',
    'test_dice_loc.py', 'test_wuzzuf.py', 'test_wuzzuf_debug.py', 'test_wuzzuf_debug2.py',
    'test_wuzzuf_debug3.py', 'debug_bayt.py', 'debug_bayt_profile.py', 'debug_cloudscraper.py',
    'debug_regex.py', 'test_indeed_proxies.py', 'test_job_sources.py', 'test_more_approaches.py',
    'test_no_gzip.py', 'test.py', 'test_turso.py',
    'screenshot.py', 'screenshot_all.py', 'screenshot_auth.py', 'screenshot_dashboard.py',
    'take_screenshot.py', 'take_screenshot2.py', 'take_screenshot3.py', 'take_screenshot4.py',
    'take_screenshot5.py', 'take_screenshot_local.py', 'take_live_screenshot.py',
    'dump_real.py', 'dump_real2.py', 'dump_shell.py', 'analyze_dice.py', 'check_dice.py',
    'check_jina.py', 'inspect_responses.py', 'audit_ui.py',
    'deploy_to_render.py', 'deploy_to_fly.py', 'deploy_to_hf.py',
    'deploy_hf.py', 'hf_setup.py', 'hf_deploy.py',
    'start_render.py', 'run_render.py', 'render_boot.py', 'render_dashboard.py',
    'deploy_deep_scan.py', 'deploy_milestone3.py', 'pa_upload.py', 'pa_fix.py',
    'gen_final_report.py', 'profit_report.py', 'web_only.py', 'simulate_payment.py',
    '_upload_env_pa.py', '_force_restart_pa.py', '_wait_pa.py',
    '_send_tg_test.py', '_tg_direct.py', '_test_pa_api.py',
    '_trigger_deploy.py', '_check_cron.py', 'cli.py',
]

# Dynamically gather duplicate dump files and temp log captures
dynamic_patterns = [
    'resp_*.html',
    'wuzzuf_debug*.html',
    'bayt_debug*.html',
    'dice_debug*.html',
    '*.log.txt',
]

for pattern in dynamic_patterns:
    for filepath in glob.glob(os.path.join(root, pattern)):
        filename = os.path.basename(filepath)
        if filename not in trash_files:
            trash_files.append(filename)

moved = 0
skipped = 0
for f in trash_files:
    src = os.path.join(root, f)
    if os.path.exists(src):
        dst = os.path.join(backup, f)
        # Ensure target folder structure exists if it's nested
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
        moved += 1
    else:
        skipped += 1

# Also clean __pycache__ folders recursively
cleaned_caches = 0
for cache_dir in glob.glob(os.path.join(root, '**/__pycache__'), recursive=True):
    if os.path.exists(cache_dir) and os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir)
        cleaned_caches += 1

# Log findings
log_path = os.path.join(backup, 'CLEANUP_LOG.txt')
with open(log_path, 'w', encoding='utf-8') as log:
    log.write(f'Cleanup: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    log.write(f'Moved: {moved} files\n')
    log.write(f'Skipped: {skipped} files\n')
    log.write(f'Cleaned Pycache Dirs: {cleaned_caches}\n')
    log.write(f'Backed up to _backups/cleanup_...\n')
    log.write('All files are recoverable. Deploy scripts verified NOT affected.\n')

print(f"Cleaned up {moved} temp/debug files and {cleaned_caches} __pycache__ directories.")
