import json
import os
import glob

brain_dir = r"C:\Users\samde\.gemini\antigravity\brain"
agent_dirs = [d for d in os.listdir(brain_dir) if os.path.isdir(os.path.join(brain_dir, d))]

for agent_id in agent_dirs:
    log_path = os.path.join(brain_dir, agent_id, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("type") == "PLANNER_RESPONSE":
                        calls = data.get("tool_calls", [])
                        for call in calls:
                            if call.get("name") == "send_message":
                                args = call.get("args", {})
                                if args.get("Recipient") == "1aee8489-c3ba-4cb9-9827-a070d3bd8d4c":
                                    print(f"--- Message from {agent_id} ---")
                                    print(args.get("Message")[:1000] + "...\n")
                except:
                    pass
