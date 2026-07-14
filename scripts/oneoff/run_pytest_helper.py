import logging
import subprocess

logger = logging.getLogger(__name__)
import os

files = [
    "tests/e2e/test_database.py",
    "tests/e2e/test_e2e_backend.py",
    "tests/e2e/test_frontend.py",
    "tests/e2e/test_r1_cover_letter.py",
    "tests/e2e/test_r2_dashboard.py",
    "tests/e2e/test_r3_scraper.py",
    "tests/e2e/test_r4_auth.py",
    "tests/e2e/test_r5_cicd.py",
    "tests/e2e/test_unauthorized.py",
]

logger.info("Running E2E test files individually...")
for f in files:
    if not os.path.exists(f):
        logger.info(f"File not found: {f}")
        continue
    logger.info(f"--- Running {f} ---")
    res = subprocess.run(
        [r"test_env\Scripts\pytest", "-v", f],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    logger.info(f"Exit code: {res.returncode}")
    if res.returncode != 0:
        logger.info(f"Error output:\n{res.stderr}\n{res.stdout[-1000:] if res.stdout else ''}")
