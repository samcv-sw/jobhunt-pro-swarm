"""
Live Interview AI Copilot & Speech Shadowing Engine.
Sub-200ms real-time question analysis, STAR-method framing, and tactical answer cues.
"""

import time
from typing import Dict, Any, List

QUESTION_PATTERNS = {
    "system_design": ["design", "architecture", "scale", "microservice", "database", "high traffic", "throughput", "latency"],
    "behavioral": ["tell me about a time", "conflict", "disagreement", "challenge", "failed", "leadership", "mistake"],
    "technical": ["how does", "explain", "complexity", "algorithm", "python", "fastapi", "webrtc", "docker", "postgres"],
    "salary": ["compensation", "salary", "expectations", "budget", "rate"]
}

class InterviewCopilot:
    def __init__(self):
        pass

    def process_live_audio_transcript(self, transcript_chunk: str, candidate_role: str = "Senior AI Engineer") -> Dict[str, Any]:
        """
        Analyzes live audio transcript chunk and generates immediate tactical interview cues.
        Latency target: < 200ms.
        """
        start_time = time.time()
        text_lower = transcript_chunk.lower().strip()

        q_type = "general"
        for cat, keywords in QUESTION_PATTERNS.items():
            if any(kw in text_lower for kw in keywords):
                q_type = cat
                break

        # Generate tactical STAR & technical bullet points
        cues = self._generate_cues(q_type, text_lower, candidate_role)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "transcript_snippet": transcript_chunk,
            "detected_question_type": q_type,
            "tactical_cues": cues,
            "latency_ms": latency_ms,
            "suggested_star_frame": {
                "S_situation": cues.get("situation", "In my previous production deployment..."),
                "T_task": cues.get("task", "I was tasked with optimizing throughput under zero cost..."),
                "A_action": cues.get("action", "I engineered a distributed P2P WASM pipeline..."),
                "R_result": cues.get("result", "Achieved 99.9% uptime with 0$ cloud overhead.")
            }
        }

    def _generate_cues(self, q_type: str, text: str, role: str) -> Dict[str, str]:
        if q_type == "system_design":
            return {
                "situation": "Scaling a multi-region SaaS platform under zero budget constraints.",
                "task": "Decouple DB writes and offload compute to browser/edge nodes.",
                "action": "Implemented event-sourcing with SQLite WAL shims & Cloudflare Workers.",
                "result": "Reduced API latency to sub-50ms with 100k daily active queries."
            }
        elif q_type == "behavioral":
            return {
                "situation": "Facing conflicting architectural priorities between speed and test coverage.",
                "task": "Align stakeholder expectations while maintaining strict 100% test pass rate.",
                "action": "Setup automated test suites and parallel CI/CD validation matrix.",
                "result": "Delivered features 2x faster with zero regression bugs."
            }
        elif q_type == "technical":
            return {
                "situation": "High memory consumption during large dataset processing.",
                "task": "Refactor codebase to run stream processing under strict limits.",
                "action": "Replaced global replacements with AST-based chunk processing and Python generators.",
                "result": "Cut RAM footprint by 85% and eliminated memory leaks."
            }
        else:
            return {
                "situation": f"Working as a {role} on mission-critical applications.",
                "task": "Deliver end-to-end autonomous software features.",
                "action": "Applied modern design patterns and comprehensive automation test suites.",
                "result": "Achieved 10/10 production readiness rating."
            }

# Global singleton instance
interview_copilot = InterviewCopilot()
