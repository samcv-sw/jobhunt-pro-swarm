import os
import subprocess
import sys
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent
LOCALES_DIR = ROOT_DIR / "locales"
BABEL_CFG = ROOT_DIR / "babel.cfg"
POT_FILE = LOCALES_DIR / "messages.pot"

def run_cmd(cmd):
    logger.debug(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=str(ROOT_DIR))
    if result.returncode != 0:
        logger.debug(f"Command failed with exit code {result.returncode}")
        exit(result.returncode)

def main():
    # 1. Ensure locales directory exists
    os.makedirs(LOCALES_DIR, exist_ok=True)

    # 2. Extract messages to .pot
    logger.debug("Extracting strings...")
    run_cmd(f'pybabel extract -F "{BABEL_CFG}" -o "{POT_FILE}" .')

    # 3. Init or update Arabic locale
    ar_po = LOCALES_DIR / "ar" / "LC_MESSAGES" / "messages.po"
    if not ar_po.exists():
        logger.debug("Initializing Arabic locale...")
        run_cmd(f'pybabel init -i "{POT_FILE}" -d "{LOCALES_DIR}" -l ar')
    else:
        logger.debug("Updating Arabic locale...")
        run_cmd(f'pybabel update -i "{POT_FILE}" -d "{LOCALES_DIR}" -l ar')

    # 4. Init or update English locale (optional but good for consistency)
    en_po = LOCALES_DIR / "en" / "LC_MESSAGES" / "messages.po"
    if not en_po.exists():
        logger.debug("Initializing English locale...")
        run_cmd(f'pybabel init -i "{POT_FILE}" -d "{LOCALES_DIR}" -l en')
    else:
        logger.debug("Updating English locale...")
        run_cmd(f'pybabel update -i "{POT_FILE}" -d "{LOCALES_DIR}" -l en')

    # 5. Compile translations to .mo
    logger.debug("Compiling translations...")
    run_cmd(f'pybabel compile -d "{LOCALES_DIR}"')
    
    logger.debug("Done! Translations are ready.")

if __name__ == "__main__":
    main()
