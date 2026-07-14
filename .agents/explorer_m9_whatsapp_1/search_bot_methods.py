import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

print("Searching methods in TelegramBot:")
with open(bot_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def cmd_" in line or "class TelegramBot" in line or "async def process_webhook_update" in line:
        print(f"Line {i+1}: {line.strip()}")
