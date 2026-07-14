import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
bot_path = os.path.join(cwd, "core", "telegram", "bot.py")

with open(bot_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's extract cmd_campaign and cmd_campaigns code to see how it lists/updates campaigns
import re

print("Extracting campaign command definitions:")
for m in re.finditer(r"async def cmd_campaigns?\(", content):
    start_pos = m.start()
    # find next async def or def
    end_pos = content.find("async def ", start_pos + 1)
    if end_pos == -1:
        end_pos = content.find("def ", start_pos + 1)
    if end_pos == -1:
        end_pos = len(content)
    snippet = content[start_pos:end_pos]
    print(snippet[:1200])
    print("=" * 60)
