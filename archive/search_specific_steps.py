# scratch/search_specific_steps.py
import os
import json
import sys

# Avoid Windows console Unicode encoding errors
sys.stdout.reconfigure(encoding='utf-8')

messages_dir = r"C:\Users\samde\.gemini\antigravity\brain\e5e5343f-d494-4f16-86cb-23ac1f1ad9da\.system_generated\messages"
subagent_id = "4a3f1eae-bcb3-4756-a588-fb18c9a24ea0"

print(f"--- Searching messages from subagent {subagent_id} ---")
for filename in os.listdir(messages_dir):
    if filename.endswith(".json") and filename not in ("cursor.json", "read.json"):
        filepath = os.path.join(messages_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("sender") == subagent_id:
                    print(f"Found message in {filename} (Timestamp: {data.get('timestamp')}):")
                    print(data.get("content"))
                    print("=" * 60)
        except Exception as e:
            pass
