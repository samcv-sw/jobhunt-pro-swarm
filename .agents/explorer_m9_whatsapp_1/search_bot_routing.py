import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

with open(bot_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Searching send and routing methods:")
for i, line in enumerate(lines):
    if "async def send(" in line or "async def handle_" in line or "async def on_message" in line or "async def route_command" in line:
        print(f"Line {i+1}: {line.strip()}")
        # print 15 lines of context
        for idx in range(i, min(i+25, len(lines))):
            print(f"  {idx+1}: {lines[idx].rstrip()}")
        print("-" * 50)
