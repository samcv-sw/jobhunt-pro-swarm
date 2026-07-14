import json
import os
import re
import sys

transcript_path = r"C:\Users\samde\.gemini\antigravity\brain\e5e5343f-d494-4f16-86cb-23ac1f1ad9da\.system_generated\logs\transcript.jsonl"
output_path = r"c:\Users\samde\Desktop\cv sam new ma3 kimi\scratch\transcript_results.txt"

print(f"Checking if transcript exists: {os.path.exists(transcript_path)}")

user_questions = []
answers = []

if os.path.exists(transcript_path):
    with open(transcript_path, 'r', encoding='utf-8') as f:
        steps = []
        for line in f:
            try:
                data = json.loads(line)
                steps.append(data)
            except Exception:
                pass
        
        with open(output_path, 'w', encoding='utf-8') as out:
            for i, step in enumerate(steps):
                content = step.get("content", "")
                if step.get("type") == "USER_INPUT" and any(q in content.lower() for q in ["3adedle", "websitet", "list", "3ende"]):
                    out.write(f"\n--- USER INPUT (Step {step.get('step_index')}) ---\n")
                    out.write(content + "\n")
                    # Find the next few MODEL steps
                    for j in range(i+1, min(i+10, len(steps))):
                        next_step = steps[j]
                        if next_step.get("source") == "MODEL" and next_step.get("content"):
                            out.write(f"--- ASSISTANT RESPONSE (Step {next_step.get('step_index')}) ---\n")
                            out.write(next_step.get("content") + "\n")
                            break

print(f"Done! Results written to {output_path}")
