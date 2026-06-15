"""
JobHunt Pro v16 — Core Modules
Swarm architecture: 200 virtual agents, multi-provider LLM & email pools.
Multi-market: MENA (Lebanon/UAE/KSA/Qatar/Kuwait) + Russia/CIS (hh.ru API).
"""

from core.agent_pool import AgentPool, VirtualAgent, AgentType, AGENT_DISTRIBUTION, AgentStats
from core.hhru_scraper import search_hhru, search_hhru_sync, resolve_area_ids, resolve_area_id, HHRU_AREA_MAP
from core.swarm_master import SwarmMaster
from core.llm_provider_pool import LLMProviderPool, LLMProvider, ProviderInstance, PROVIDER_CONFIGS
from core.email_rotator_pool import EmailRotatorPool, EmailSenderClient, EmailAccount
from core.ats_matcher import ATSMatcher, analyze_with_groq, full_ats_analysis, analyze_with_groq_async
from core.ai_conversation import AIConversationEngine, get_engine
from core.resume_optimizer import ResumeOptimizer, parse_job_keywords, optimize_resume, generate_ats_resume, ATSOptimizationResult

__all__ = [
    # Agent Pool
    "AgentPool",
    "VirtualAgent",
    "AgentType",
    "AGENT_DISTRIBUTION",
    "AgentStats",
    # Swarm Master
    "SwarmMaster",
    # LLM Provider Pool
    "LLMProviderPool",
    "LLMProvider",
    "ProviderInstance",
    "PROVIDER_CONFIGS",
    # Email Rotator Pool
    "EmailRotatorPool",
    "EmailSenderClient",
    "EmailAccount",
    # ATS Matcher
    "ATSMatcher",
    "analyze_with_groq",
    "full_ats_analysis",
    "analyze_with_groq_async",
    # AI Conversation Engine
    "AIConversationEngine",
    "get_engine",
    # ATS Resume Optimizer
    "ResumeOptimizer",
    "parse_job_keywords",
    "optimize_resume",
    "generate_ats_resume",
    "ATSOptimizationResult",
    # hh.ru Scraper (Russia/CIS market)
    "search_hhru",
    "search_hhru_sync",
    "resolve_area_ids",
    "resolve_area_id",
    "HHRU_AREA_MAP",
]

