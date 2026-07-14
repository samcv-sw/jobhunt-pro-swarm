import logging
import os

logger = logging.getLogger(__name__)
import re

project_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
count = 0

for root, dirs, files in os.walk(project_dir):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = content.replace("import core.telegram.bot as telegram_bot", "import core.telegram.bot as telegram_bot")
            new_content = new_content.replace("from core.telegram import bot as telegram_bot", "from core.telegram import bot as telegram_bot")
            new_content = new_content.replace("from core.telegram.bot import", "from core.telegram.bot import")
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
                logger.info(f"Updated imports in: {file}")

logger.info(f"Total files updated: {count}")
