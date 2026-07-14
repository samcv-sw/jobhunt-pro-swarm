import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

with open(bot_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Occurrences of _auto_running:")
for i, line in enumerate(lines):
    if "_auto_running" in line:
        print(f"Line {i+1}: {line.strip()}")
        # print 3 lines before and after
        start = max(0, i - 3)
        end = min(len(lines), i + 4)
        for j in range(start, end):
            if j != i:
                print(f"  {j+1}: {lines[j].rstrip()}")
        print("-" * 50)
