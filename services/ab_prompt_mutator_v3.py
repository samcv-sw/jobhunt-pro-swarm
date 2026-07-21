"""
AB Prompt Mutator Service v3 - Self-Healing Prompt Optimizer
Tracks response/conversion rates and auto-mutates outreach & tailoring prompts using genetic heuristic variation.
"""

import math
import random
from typing import Dict, Any, List, Optional

DEFAULT_PROMPTS = {
    "cold_email_v1": "Dear {hiring_manager}, I noticed your opening for {role} at {company}. My background in {key_skill} matches your needs.",
    "cold_email_v2": "Hi {hiring_manager}, driving results in {key_skill} is my core expertise. I'd love to contribute to {company}'s {role} team.",
    "cv_tailor_v1": "Highlight metrics, quantify impact in {key_skill}, and optimize for {role} keywords.",
    "cv_tailor_v2": "Focus on leadership achievements, scalable architecture in {key_skill}, and alignment with {company}'s stack."
}

class ABPromptMutator:
    def __init__(self):
        self.stats: Dict[str, Dict[str, Any]] = {
            pid: {"sent": 10, "replies": 2, "conversions": 1, "prompt": prompt}
            for pid, prompt in DEFAULT_PROMPTS.items()
        }

    def record_metrics(self, prompt_id: str, sent_delta: int = 1, reply_delta: int = 0, conversion_delta: int = 0) -> Dict[str, Any]:
        if prompt_id not in self.stats:
            self.stats[prompt_id] = {"sent": 0, "replies": 0, "conversions": 0, "prompt": ""}
        s = self.stats[prompt_id]
        s["sent"] += sent_delta
        s["replies"] += reply_delta
        s["conversions"] += conversion_delta
        return self.get_prompt_performance(prompt_id)

    def get_prompt_performance(self, prompt_id: str) -> Dict[str, Any]:
        s = self.stats.get(prompt_id, {"sent": 0, "replies": 0, "conversions": 0})
        sent = max(s["sent"], 1)
        reply_rate = round(s["replies"] / sent, 4)
        conv_rate = round(s["conversions"] / sent, 4)
        score = round(reply_rate * 0.6 + conv_rate * 0.4, 4)
        return {
            "prompt_id": prompt_id,
            "sent": sent,
            "replies": s["replies"],
            "conversions": s["conversions"],
            "reply_rate": reply_rate,
            "conversion_rate": conv_rate,
            "performance_score": score
        }

    def mutate_prompt(self, base_prompt_id: str) -> Dict[str, Any]:
        if base_prompt_id not in self.stats:
            base_prompt = DEFAULT_PROMPTS.get(base_prompt_id, "Optimize resume for {role}")
        else:
            base_prompt = self.stats[base_prompt_id]["prompt"]

        variations = [
            f"{base_prompt} Ensure strong call-to-action with metric evidence.",
            f"Action-oriented: {base_prompt} Emphasize direct ROI and velocity.",
            f"Concise & high impact: {base_prompt} Keep tone executive and precise."
        ]
        new_prompt = random.choice(variations)
        new_id = f"{base_prompt_id}_mutated_{random.randint(100, 999)}"
        self.stats[new_id] = {"sent": 1, "replies": 0, "conversions": 0, "prompt": new_prompt}
        return {"new_prompt_id": new_id, "mutated_prompt": new_prompt, "base_prompt_id": base_prompt_id}

    def get_best_prompt(self, category: str = "cold_email") -> Dict[str, Any]:
        matching = {pid: self.get_prompt_performance(pid) for pid in self.stats if category in pid}
        if not matching:
            matching = {pid: self.get_prompt_performance(pid) for pid in self.stats}
        best_id = max(matching, key=lambda k: matching[k]["performance_score"])
        return {**matching[best_id], "prompt": self.stats[best_id]["prompt"]}

ab_prompt_mutator_v3 = ABPromptMutator()
