"""
JobHunt Pro - Job Board Aggregator
Indeed, Glassdoor, LinkedIn Jobs, Monster, ZipRecruiter integration
"""
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class JobBoardConfig:
    """Configuration for job board APIs."""

    BOARDS = {
        "indeed": {
            "name": "Indeed",
            "api_url": "https://api.indeed.com/ads/apisearch",
            "free_tier": {"daily Searches": 25, "daily Applications": 50},
            "paid_tier": {"daily_searches": 500, "daily_applications": 1000},
            "cost_per_hire": 100,
            "priority": 1,
        },
        "glassdoor": {
            "name": "Glassdoor",
            "api_url": "https://api.glassdoor.com/api/api.htm",
            "free_tier": {"daily_searches": 10, "daily_applications": 20},
            "paid_tier": {"daily_searches": 200, "daily_applications": 500},
            "cost_per_hire": 150,
            "priority": 2,
        },
        "linkedin_jobs": {
            "name": "LinkedIn Jobs",
            "api_url": "https://api.linkedin.com/v2/jobs",
            "free_tier": {"daily_searches": 5, "daily_applications": 10},
            "paid_tier": {"daily_searches": 100, "daily_applications": 300},
            "cost_per_hire": 200,
            "priority": 3,
        },
        "monster": {
            "name": "Monster",
            "api_url": "https://api.monster.com/v1/jobs",
            "free_tier": {"daily_searches": 20, "daily_applications": 40},
            "paid_tier": {"daily_searches": 300, "daily_applications": 700},
            "cost_per_hire": 80,
            "priority": 4,
        },
        "ziprecruiter": {
            "name": "ZipRecruiter",
            "api_url": "https://api.ziprecruiter.com/jobs",
            "free_tier": {"daily_searches": 15, "daily_applications": 30},
            "paid_tier": {"daily_searches": 250, "daily_applications": 600},
            "cost_per_hire": 120,
            "priority": 5,
        },
        # ── 2025 Additional Boards ──────────────────────────────────────────
        "adzuna": {
            "name": "Adzuna",
            "api_url": "https://api.adzuna.com/v1/api/jobs",
            "free_tier": {"daily_searches": 100, "daily_applications": 200},
            "paid_tier": {"daily_searches": 1000, "daily_applications": 5000},
            "cost_per_hire": 0,  # Aggregator — no direct hire cost
            "priority": 6,
            "notes": "Good coverage for UK, AU, CA, MENA regions. Free API key available.",
        },
        "jsearch": {
            "name": "JSearch (RapidAPI)",
            "api_url": "https://jsearch.p.rapidapi.com/search",
            "free_tier": {"daily_searches": 10, "daily_applications": 0},
            "paid_tier": {"daily_searches": 500, "daily_applications": 0},
            "cost_per_hire": 0,
            "priority": 7,
            "notes": "Aggregates LinkedIn, Indeed, Glassdoor. Best for remote + GCC searches.",
        },
        "remotive": {
            "name": "Remotive",
            "api_url": "https://remotive.com/api/remote-jobs",
            "free_tier": {"daily_searches": 999, "daily_applications": 0},
            "paid_tier": {"daily_searches": 999, "daily_applications": 0},
            "cost_per_hire": 0,
            "priority": 8,
            "notes": "100% free REST API. Ideal for remote network/cloud engineering roles.",
        },
        "bundesagentur": {
            "name": "Bundesagentur für Arbeit (Germany)",
            "api_url": "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs",
            "free_tier": {"daily_searches": 999, "daily_applications": 0},
            "paid_tier": {"daily_searches": 999, "daily_applications": 0},
            "cost_per_hire": 0,
            "priority": 9,
            "notes": "Official German Federal Employment Agency. Free API, no key needed. Great for EU expansion.",
        },
    }


class JobBoardAggregator:
    """Aggregate jobs from multiple boards."""

    def __init__(self):
        self.config = JobBoardConfig()
        self.results_cache = {}
        self.stats = {board: {"searches": 0, "applications": 0, "hires": 0}
                      for board in self.config.BOARDS}

    def get_board_status(self) -> Dict:
        """Get status of all job boards."""
        return {
            board: {
                "name": info["name"],
                "free_limit": info["free_tier"],
                "priority": info["priority"],
                "cost_per_hire": info["cost_per_hire"],
                "stats": self.stats.get(board, {"searches": 0, "applications": 0, "hires": 0}),
                "notes": info.get("notes", ""),
            }
            for board, info in self.config.BOARDS.items()
        }

    def get_board_by_priority(self, max_cost_per_hire: int = 999) -> List[str]:
        """Return board IDs sorted by priority, filtered by cost per hire."""
        filtered = [
            (board, info["priority"])
            for board, info in self.config.BOARDS.items()
            if info.get("cost_per_hire", 0) <= max_cost_per_hire
        ]
        return [b for b, _ in sorted(filtered, key=lambda x: x[1])]

    def estimate_monthly_cost(self, applications_per_month: int = 500) -> Dict:
        """Estimate monthly job board costs."""
        costs = {}
        for board, info in self.config.BOARDS.items():
            # Assume 10% conversion from application to hire
            hires = int(applications_per_month * 0.1)
            cost = hires * info["cost_per_hire"]
            costs[board] = {
                "board": info["name"],
                "estimated_hires": hires,
                "cost_per_hire": info["cost_per_hire"],
                "monthly_cost": cost,
            }

        total = sum(c["monthly_cost"] for c in costs.values())
        return {"boards": costs, "total_monthly": total}


class JobMatcher:
    """AI-powered job matching and scoring."""

    def __init__(self):
        self.skill_weights = {
            # Core network skills
            "cisco": 10, "mikrotik": 8, "ubiquiti": 7, "fortinet": 9,
            "juniper": 8, "ospf": 7, "bgp": 7, "mpls": 6,
            "vpn": 5, "firewalls": 8, "network security": 9,
            "aws": 6, "azure": 6, "cloud networking": 7,
            "python": 5, "ansible": 5, "terraform": 5,
            # 2025 emerging skills
            "sd-wan": 9, "sase": 9, "ztna": 8, "zero trust": 8,
            "kubernetes": 7, "docker": 6, "devops": 6, "devsecops": 8,
            "ebpf": 8, "cilium": 7, "platform engineering": 8,
            "cnapp": 8, "cspm": 7, "ciem": 7,
            "gitops": 6, "argocd": 6, "helm": 5,
            "opentelemetry": 6, "observability": 6, "sre": 7,
            "llm": 5, "aiops": 6, "5g": 7, "openran": 7,
        }

    def score_job_match(self, job: Dict, candidate_skills: List[str]) -> Dict:
        """Score how well a job matches the candidate."""
        try:
            job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('snippet', '')}".lower()
            score = 0
            matched_skills = []

            for skill, weight in self.skill_weights.items():
                if skill in job_text:
                    score += weight
                    matched_skills.append(skill)

            max_possible = sum(self.skill_weights.values())
            match_pct = round((score / max_possible) * 100, 1) if max_possible > 0 else 0.0

            return {
                "match_score": min(100, match_pct),
                "matched_skills": matched_skills,
                "salary_match": self._check_salary(job),
                "location_match": self._check_location(job),
                "overall": self._get_overall_rating(match_pct),
            }
        except Exception as e:
            logger.warning(f"[JobMatcher] score_job_match failed: {e}")
            return {
                "match_score": 0,
                "matched_skills": [],
                "salary_match": True,
                "location_match": False,
                "overall": "low",
            }

    def _check_salary(self, job: Dict) -> bool:
        salary_text = job.get("salary", "")
        if not salary_text:
            return True  # No salary info = could match
        return True  # Simplified

    def _check_location(self, job: Dict) -> bool:
        location = job.get("location", "").lower()
        preferred = ["remote", "lebanon", "uae", "dubai", "saudi", "qatar", "gcc"]
        return any(p in location for p in preferred)

    def _get_overall_rating(self, pct: float) -> str:
        if pct >= 70: return "excellent"
        if pct >= 50: return "good"
        if pct >= 30: return "fair"
        return "low"


# ── Global instances ──────────────────────────────────────────
job_board_aggregator = JobBoardAggregator()
job_matcher = JobMatcher()
