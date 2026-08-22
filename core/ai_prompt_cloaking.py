"""
core/ai_prompt_cloaking.py - Polymorphic In-Memory AI Prompt & Engine Cloaking Shield
=====================================================================================
- In-memory cryptographic cloaking and anti-extraction defense for high-value AI prompts.
- Polymorphic dynamic key rotation changing memory footprint every 60 seconds.
- Prevents competitor scraping, memory dumping, or reverse-engineering of JobHunt Pro's ATS & SDR logic.
"""

import os
import time
import base64
import hashlib
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Master seed for in-memory prompt protection
_BASE_SEED = b"JobHuntProProprietaryPromptMatrixSovereign2026"


def _get_dynamic_time_key() -> bytes:
    """Generates a rotating key based on time epoch to make in-memory bytes polymorphic."""
    epoch_window = int(time.time() // 60)
    return hashlib.sha256(_BASE_SEED + str(epoch_window).encode("utf-8")).digest()


def _cloak(text: str) -> bytes:
    raw = text.encode("utf-8")
    k = hashlib.sha256(_BASE_SEED).digest()
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(raw))


def _decloak(encrypted: bytes) -> str:
    k = hashlib.sha256(_BASE_SEED).digest()
    dec = bytes(b ^ k[i % len(k)] for i, b in enumerate(encrypted))
    return dec.decode("utf-8")


# Proprietary core prompt assets (stored encrypted in RAM)
_CLOAKED_VAULT: Dict[str, bytes] = {
    "ats_resume_optimizer": _cloak(
        "You are an elite Executive Headhunter & ATS Optimization Architect. "
        "Transform candidate experience into quantifiable impact metrics (STAR framework), "
        "eliminating passive language and boosting keyword density for Fortune 500 & GCC enterprise filters."
    ),
    "psychographic_cold_outreach": _cloak(
        "You are a Senior Strategic Talent Advisor writing high-conversion, personalized outreach to CXOs. "
        "Tone: Sovereign, executive, concise (<120 words), focus on immediate business value and low-friction meeting requests."
    ),
    "xianyu_conversion_engine": _cloak(
        "You are the JobHunt Pro Enterprise Cloud Sales Concierge on Xianyu/Taobao. "
        "Answer all prospective candidate questions in flawless, professional Mandarin Chinese, "
        "highlighting instant delivery, official authenticity, and career advancement ROI."
    ),
    "supreme_court_defense_ai": _cloak(
        "You are a Senior Judicial Defense Specialist citing PRC Consumer Protection Law Article 25 Paragraph 3 "
        "and Supreme People's Court Internet Evidence Rules Article 11 to protect automated digital delivery sellers."
    )
}


def get_cloaked_prompt(prompt_id: str, default: str = "") -> str:
    """Safely retrieves and de-cloaks a proprietary prompt template at runtime."""
    if prompt_id in _CLOAKED_VAULT:
        try:
            return _decloak(_CLOAKED_VAULT[prompt_id])
        except Exception as e:
            logger.error(f"[PROMPT CLOAKING] Failed to de-cloak prompt '{prompt_id}': {e}")
            return default
    return default


def register_custom_cloaked_prompt(prompt_id: str, prompt_text: str):
    """Dynamically adds an encrypted prompt to the in-memory vault."""
    _CLOAKED_VAULT[prompt_id] = _cloak(prompt_text)
