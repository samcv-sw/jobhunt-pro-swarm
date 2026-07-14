import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

with open(bot_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(1788 - 1, min(1806, len(lines))):
    print(f"{idx + 1}: {lines[idx].rstrip()}")
