import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

with open(bot_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_lines(start, end):
    print(f"=== Lines {start} to {end} ===")
    for idx in range(start - 1, min(end, len(lines))):
        print(f"{idx + 1}: {lines[idx].rstrip()}")

print_lines(1185, 1205)
print_lines(1330, 1400)
print_lines(1770, 1795)
