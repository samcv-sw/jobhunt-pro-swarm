"""
core/ml_ranking.py — Unified ML Job-Candidate Ranking Engine

Brings JobHunt Pro to big-platform (LinkedIn/Indeed) automation parity by
fusing three complementary ML signals into a single, deterministic,
production-grade match score:

  1. TF-IDF + Cosine Similarity (local, zero-cost, instant) — vectorizes the
     candidate's ACTUAL CV text against the job description (unlike the legacy
     hardcoded CANDIDATE_PROFILE in ai_tailor._cosine_similarity_score).
  2. Gemini text-embedding-004 (768-dim) semantic similarity — used when a
     GEMINI_API_KEY is present; gracefully degrades to TF-IDF-only when absent
     or on network failure (semantic_cache.get_embedding returns []).
  3. Keyword / skill overlap — the proven lexical signal from the existing
     /api/v1/job-match-score endpoint, retained for transparency.

Design invariants (Omni-Architecture):
  * Zero hard external dependencies — scikit-learn is optional; a pure-Python
    cosine fallback keeps the engine alive if sklearn is missing.
  * Graceful degradation — never raises; always returns a usable score.
  * Monomorphic hot paths — stable dict shapes for predictable execution.
  * O(1) embedding cache — reuses semantic_cache.get_embedding's lru_cache.
"""
from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional

import config

logger = logging.getLogger("ml_ranking")

# ---------------------------------------------------------------------------
# Optional ML dependencies (scikit-learn). Graceful fallback if absent.
# ---------------------------------------------------------------------------
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _HAS_SKLEARN = True
except Exception:  # pragma: no cover - environment dependent
    _HAS_SKLEARN = False
    logger.warning("[ML_RANKING] scikit-learn unavailable; using pure-Python cosine fallback.")

# Common technical keywords for lexical overlap (mirrors legacy endpoint).
_COMMON_TECH = [
    "python", "java", "javascript", "sql", "aws", "azure", "docker", "kubernetes",
    "linux", "git", "agile", "scrum", "react", "angular", "node", "typescript",
    "cisco", "juniper", "fortinet", "palo alto", "bgp", "ospf", "mpls", "vpn",
    "firewall", "ccna", "ccnp", "sd-wan", "vlan", "tcp/ip", "dns", "dhcp",
    "mikrotik", "ubiquiti", "network", "security", "cloud", "devops", "ci/cd",
    "terraform", "ansible", "jenkins", "grafana", "prometheus", "nginx", "apache",
    "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "kafka",
    "power bi", "tableau", "excel", "salesforce", "sap", "oracle",
    "project management", "pmp", "prince2", "itil", "servicenow", "routing",
    "switching", "wan", "lan", "nat", "qos", "ipv6", "aruba", "meraki", "sophos",
    "checkpoint", "f5", "citrix",
]


def _pure_cosine(a: List[float], b: List[float]) -> float:
    """Pure-Python cosine similarity (fallback when sklearn missing)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _tfidf_cosine(candidate_text: str, job_text: str) -> float:
    """Local TF-IDF cosine similarity between candidate CV and job text."""
    if not candidate_text.strip() or not job_text.strip():
        return 0.0
    if _HAS_SKLEARN:
        try:
            vec = TfidfVectorizer(stop_words="english")
            mat = vec.fit_transform([candidate_text, job_text])
            return float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"[ML_RANKING] TF-IDF failed: {e}")
            return 0.0
    # Fallback: bag-of-words cosine on shared vocabulary.
    def _bow(t: str) -> Dict[str, int]:
        words = re.findall(r"[a-z0-9+/]+", t.lower())
        d: Dict[str, int] = {}
        for w in words:
            d[w] = d.get(w, 0) + 1
        return d

    ca, ja = _bow(candidate_text), _bow(job_text)
    vocab = set(ca) | set(ja)
    va = [float(ca.get(w, 0)) for w in vocab]
    vb = [float(ja.get(w, 0)) for w in vocab]
    return _pure_cosine(va, vb)


def _embedding_cosine(text_a: str, text_b: str) -> Optional[float]:
    """Gemini embedding cosine; None if embeddings unavailable."""
    try:
        from core.semantic_cache import get_embedding
    except Exception:  # pragma: no cover
        return None
    ea, eb = get_embedding(text_a), get_embedding(text_b)
    if not ea or not eb or len(ea) != len(eb):
        return None
    return _pure_cosine(ea, eb)


class MLRankingEngine:
    """Unified job-candidate ML ranking engine (singleton)."""

    def __init__(self) -> None:
        self.banned_titles = getattr(config, "BANNED_TITLES", [])
        self.skills = getattr(config, "SKILLS", [])

    # ------------------------------------------------------------------
    def score_job_match(
        self,
        cv_text: str,
        job_title: str,
        job_description: str,
        user_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compute a unified ML match score.

        Returns a stable dict consumed by the API layer. Never raises.
        """
        cv_lower = (cv_text or "").lower()
        jd_lower = (job_description or "").lower()
        title_lower = (job_title or "").lower()

        # --- Signal 1: TF-IDF cosine (always available) ---
        cosine_score = _tfidf_cosine(cv_lower, f"{title_lower} {jd_lower}")
        model_used = "tfidf"

        # --- Signal 2: Gemini embedding cosine (optional) ---
        embedding_score: Optional[float] = None
        if getattr(config, "GEMINI_API_KEY", ""):
            emb = _embedding_cosine(cv_text, f"{job_title} {job_description}")
            if emb is not None:
                embedding_score = emb
                model_used = "gemini-embedding+tfidf"

        # --- Signal 3: lexical keyword/skill overlap ---
        tech_keywords = set()
        for kw in _COMMON_TECH:
            if kw in jd_lower:
                tech_keywords.add(kw)
        for m in re.finditer(r"\b[A-Z]{2,6}\b", job_description or ""):
            w = m.group().lower()
            if w not in ("the", "and", "for", "our", "you", "are", "all"):
                tech_keywords.add(w)

        keyword_matches = [kw.upper() for kw in tech_keywords if kw in cv_lower]
        missing_keywords = [kw.upper() for kw in tech_keywords if kw not in cv_lower]

        user_skills_l = [s.strip().lower() for s in (user_skills or []) if s and s.strip()]
        skill_count = sum(1 for us in user_skills_l if us and us in jd_lower)
        skill_pct = round((skill_count / max(len(user_skills_l), 1)) * 100)

        # --- Fusion: weighted blend of ML + lexical signals ---
        # Cosine contributes up to 55, embedding up to 15 (if present),
        # lexical keyword overlap up to 30, skill overlap up to 10.
        kw_score = round((len(keyword_matches) / max(len(tech_keywords), 1)) * 30)
        cosine_points = min(int(cosine_score * 55), 55)
        embed_points = 0
        if embedding_score is not None:
            embed_points = min(int(embedding_score * 15), 15)
        match_score = min(
            cosine_points + embed_points + kw_score + int(min(skill_pct * 0.2, 10)), 100
        )

        # --- Banned-title penalty (anti-spam / wrong-role guard) ---
        for banned in self.banned_titles:
            if banned.lower() in title_lower:
                match_score = max(0, match_score - 60)
                break

        # --- Gaps & recommendation ---
        gaps: List[str] = []
        if missing_keywords:
            gaps.append("Missing keywords: " + ", ".join(missing_keywords[:5]))
        if skill_pct < 50:
            gaps.append(f"Only {skill_pct}% of your listed skills match this job")
        if not gaps:
            gaps.append("Great match! Your skills align well with this position.")

        if match_score >= 80:
            rec = "Strong match! Consider this a high-priority application."
        elif match_score >= 60:
            rec = "Good match. Tailor your resume to highlight matching keywords."
        elif match_score >= 40:
            rec = "Moderate match. Use Resume Tailor to optimize your CV for this role."
        else:
            rec = "Low match. Review job requirements and consider upskilling."

        return {
            "match_score": match_score,
            "skill_match_pct": skill_pct,
            "keyword_matches": keyword_matches[:10],
            "missing_keywords": missing_keywords[:8],
            "skills_gaps": gaps,
            "recommendation": rec,
            "is_fallback": model_used == "tfidf" and not getattr(config, "GEMINI_API_KEY", ""),
            "cosine_score": round(cosine_score, 4),
            "embedding_score": round(embedding_score, 4) if embedding_score is not None else None,
            "model_used": model_used,
        }


# Global singleton (import-safe, zero side effects).
ml_ranking_engine = MLRankingEngine()
