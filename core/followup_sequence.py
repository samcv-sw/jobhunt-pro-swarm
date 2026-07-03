"""
AUTOMATED FOLLOW-UP SEQUENCE
3x response rate through strategic follow-ups
Day 3: Soft check, Day 7: Value-add, Day 14: Final push
"""

import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Lazy imports for AI-powered nudge (optional)
try:
    import importlib

    _HAS_AI = True
except ImportError:
    _HAS_AI = False

logger = logging.getLogger(__name__)

FOLLOWUP_STAGES = {
    3: {
        "name": "soft_check",
        "subject": "Following up: {role} at {company}",
        "body": """Dear {contact},

I hope this message finds you well. I wanted to follow up on my application for the {role} position at {company} that I submitted on {date}.

I understand you're likely reviewing many applications, and I just wanted to make sure my materials reached you successfully. I remain very enthusiastic about this opportunity and would welcome the chance to discuss how my 15+ years of experience in SD-WAN, network security, and cloud networking could contribute to your team.

Thank you for your time and consideration.

Best regards,
Sam Salameh
CCNP | NSE 4-7 | AWS Certified | 15+ Years Network Engineering""",
    },
    7: {
        "name": "value_add",
        "subject": "Re: {role} - SD-WAN & Security expertise",
        "body": """Dear {contact},

I wanted to share some additional thoughts regarding the {role} position at {company}.

Since submitting my application, I've been reflecting on how my specific expertise could benefit {company}:

• SD-WAN & SASE: Architected solutions across 50+ sites, reducing WAN costs by 45%
• Zero Trust Security: Implemented ZTNA for 2,000+ users across 10+ countries
• Network Automation: Python/Ansible/Terraform pipelines reducing deployment time by 40%
• Cloud Networking: Migrated 100+ servers to AWS/Azure with 99.99% uptime
• Multi-Vendor: Cisco, Fortinet, MikroTik, Palo Alto, Juniper, Aruba

I'm confident I could make an immediate impact on your network infrastructure and security posture.

I'd welcome the opportunity to discuss this further at your convenience.

Best regards,
Sam Salameh
CCNP | NSE 4-7 | AWS Certified | 15+ Years Network Engineering""",
    },
    14: {
        "name": "final_push",
        "subject": "Still interested: {role} at {company}",
        "body": """Dear {contact},

I understand you may have moved forward with other candidates, but I wanted to express my continued interest in the {role} position at {company}.

My expertise in SD-WAN architecture, Zero Trust security, network automation, and multi-cloud networking remains highly relevant for today's infrastructure challenges. I've successfully managed $5M+ budgets, led teams of 12 engineers, and delivered 99.99% uptime across 200+ locations.

I'm flexible regarding start date and open to discussing the role in whatever format works best for you. I'd also be happy to provide references or additional portfolio materials.

Thank you for considering my application.

Best regards,
Sam Salameh
CCNP | NSE 4-7 | AWS Certified | 15+ Years Network Engineering""",
    },
}

FOLLOWUP_FILE = Path("cache/followup_tracker.json")
FOLLOWUP_FILE.parent.mkdir(parents=True, exist_ok=True)


class FollowUpSequence:
    """Manage automated follow-up sequences for job applications."""

    def __init__(self):
        self.tracker = self._load()

    def _load(self) -> Dict:
        try:
            if FOLLOWUP_FILE.exists():
                with open(FOLLOWUP_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Followup load failed: {e}")
        return {"applications": {}}

    def _save(self):
        try:
            with open(FOLLOWUP_FILE, "w") as f:
                json.dump(self.tracker, f, indent=2)
        except Exception as e:
            logger.warning(f"Followup save failed: {e}")

    def register_application(
        self, company: str, email: str, role: str, applied_date: str = None
    ):
        """Register a new application for follow-up tracking."""
        key = f"{company}_{email}"
        if key not in self.tracker["applications"]:
            self.tracker["applications"][key] = {
                "company": company,
                "email": email,
                "role": role,
                "applied_date": applied_date or datetime.now().isoformat(),
                "followups_sent": [],
                "next_followup_day": 3,
                "status": "active",
            }
            self._save()
            logger.info(f"Registered follow-up tracking for {company}")

    def get_due_followups(self) -> List[Dict]:
        """Get all applications that need a follow-up."""
        due = []
        now = datetime.now()

        for key, app in self.tracker["applications"].items():
            if app["status"] != "active":
                continue

            applied = datetime.fromisoformat(app["applied_date"])
            days_since = (now - applied).days
            next_day = app["next_followup_day"]

            if days_since >= next_day and next_day in FOLLOWUP_STAGES:
                stage = FOLLOWUP_STAGES[next_day]
                due.append(
                    {
                        "key": key,
                        "company": app["company"],
                        "email": app["email"],
                        "role": app["role"],
                        "applied_date": app["applied_date"],
                        "days_since": days_since,
                        "stage": stage["name"],
                        "subject": stage["subject"],
                        "body": stage["body"],
                        "followup_day": next_day,
                    }
                )

        return due

    def mark_followup_sent(self, key: str):
        """Mark a follow-up as sent and schedule the next one."""
        if key in self.tracker["applications"]:
            app = self.tracker["applications"][key]
            app["followups_sent"].append(
                {
                    "date": datetime.now().isoformat(),
                    "stage": FOLLOWUP_STAGES.get(app["next_followup_day"], {}).get(
                        "name", "unknown"
                    ),
                }
            )

            # Schedule next follow-up
            current_day = app["next_followup_day"]
            next_stages = [d for d in FOLLOWUP_STAGES.keys() if d > current_day]
            if next_stages:
                app["next_followup_day"] = min(next_stages)
            else:
                app["status"] = "completed"

            self._save()
            logger.info(
                f"Follow-up marked as sent for {key}, next stage: day {app.get('next_followup_day', 'done')}"
            )

    def get_stats(self) -> Dict:
        """Get follow-up statistics."""
        apps = self.tracker["applications"]
        return {
            "total_tracked": len(apps),
            "active": sum(1 for a in apps.values() if a["status"] == "active"),
            "completed": sum(1 for a in apps.values() if a["status"] == "completed"),
            "total_followups_sent": sum(
                len(a["followups_sent"]) for a in apps.values()
            ),
        }

    # ── PORTED FROM CHRONOS: AI-powered nudge generation ────────────────────

    def generate_ai_nudge(
        self, company: str, role: str, followup_number: int = 1
    ) -> Optional[str]:
        """[PORTED FROM CHRONOS] Generate a personalized follow-up body using AI.

        Falls back to static templates if AI is unavailable.
        Returns HTML body string or None.
        """
        try:
            # Try to use JHP's AI infrastructure
            for module_name in [
                "core.llm_provider_pool",
                "core.multi_ai_fallback",
                "core.ai_tailor",
            ]:
                try:
                    mod = importlib.import_module(module_name)
                    if hasattr(mod, "generate_text"):
                        prompt = f"""You are a professional job application follow-up writer. Write a short, polite follow-up email body (HTML, 3-4 sentences) for a {role} position at {company}. This is follow-up #{followup_number}. Make it professional, warm, and concise. Use <p> tags. Return ONLY the HTML body, no explanations."""
                        result = mod.generate_text(prompt)
                        if result and len(str(result)) > 50:
                            logger.info(f"[AI-NUDGE] Generated follow-up for {company}")
                            return str(result)
                    elif hasattr(mod, "generate_response"):
                        result = mod.generate_response(
                            f"Write a brief follow-up email (HTML, 3-4 <p> tags) for {role} at {company}, follow-up #{followup_number}."
                        )
                        if result and len(str(result)) > 50:
                            logger.info(
                                f"[AI-NUDGE] Generated follow-up via {module_name}"
                            )
                            return str(result)
                except (ImportError, AttributeError, Exception) as e:
                    logger.debug(f"[AI-NUDGE] {module_name} unavailable: {e}")
                    continue

            # Fallback: try config-based AI agent
            try:
                import config

                gemini_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv(
                    "GEMINI_API_KEY", ""
                )
                groq_key = getattr(config, "GROQ_API_KEY", "") or os.getenv(
                    "GROQ_API_KEY", ""
                )

                if gemini_key:
                    import google.generativeai as genai

                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    prompt = f"Write a short follow-up email (HTML body only, 3-4 <p> tags) for {role} position at {company}, follow-up #{followup_number}. Professional and concise."
                    response = model.generate_content(prompt)
                    if response and response.text and len(response.text) > 50:
                        logger.info(f"[AI-NUDGE] Gemini nudge for {company}")
                        return response.text

                if groq_key:
                    import httpx

                    resp = httpx.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": f"Write a brief follow-up email (HTML body, 3-4 <p> tags) for {role} at {company}, follow-up #{followup_number}. Return ONLY the HTML body.",
                                }
                            ],
                            "temperature": 0.7,
                        },
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        if len(content) > 50:
                            logger.info(f"[AI-NUDGE] Groq nudge for {company}")
                            return content
            except Exception as e:
                logger.debug(f"[AI-NUDGE] Config-based AI failed: {e}")

        except Exception as e:
            logger.debug(f"[AI-NUDGE] AI generation failed: {e}")

        return None

    def get_followup_body(
        self,
        company: str,
        role: str,
        followup_number: int,
        days_since: int,
        contact_name: str = "Hiring Team",
    ) -> str:
        """[PORTED FROM CHRONOS] Get follow-up body — AI-generated if possible, static template otherwise."""
        # Try AI first
        ai_body = self.generate_ai_nudge(company, role, followup_number)
        if ai_body:
            return ai_body

        # Fall back to static template - map followup_number to stage day
        stage_days = sorted(FOLLOWUP_STAGES.keys())  # [3, 7, 14]
        if followup_number <= 0:
            stage_day = stage_days[0]
        elif followup_number > len(stage_days):
            stage_day = stage_days[-1]  # Last stage for followups beyond 3
        else:
            stage_day = stage_days[followup_number - 1]  # 1->3, 2->7, 3->14

        stage = FOLLOWUP_STAGES.get(stage_day, FOLLOWUP_STAGES[3])
        date_str = (datetime.now() - timedelta(days=days_since)).strftime("%Y-%m-%d")

        body = stage["body"].format(
            contact=contact_name, company=company, role=role, date=date_str
        )
        # Convert plain text to HTML paragraphs
        paragraphs = [f"<p>{p.strip()}</p>" for p in body.split("\n\n") if p.strip()]
        return "\n".join(paragraphs)


# Global instance
followup_sequence = FollowUpSequence()
