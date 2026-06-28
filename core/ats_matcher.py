"""
ATS Resume Match Score — JobHunt Pro
Algorithmic resume vs job description analyzer (Jobscan alternative).
Plus Groq-enhanced deep analysis for maximum accuracy.

Features:
  - Keyword extraction with n-gram support
  - Weighted scoring (industry-specific boosts)
  - Partial/fuzzy matching via SequenceMatcher
  - Actionable ATS optimization tips
  - Groq AI deep analysis fallback
  - Telegram command hook (/ats_score)
  - FastAPI endpoint helpers
"""

import re
import os
import json
import logging
import itertools
from typing import Dict, List, Tuple, Optional
from collections import Counter

# Globally precompiled regex for normalization
NORMALIZE_RE = re.compile(r'[^\w\s\-+#./]')

# Global persistent clients for connection pooling
_sync_client = None
_async_client = None

def _get_sync_client():
    global _sync_client
    import httpx
    if _sync_client is None or _sync_client.is_closed:
        _sync_client = httpx.Client(timeout=30)
    return _sync_client

def _get_async_client():
    global _async_client
    import httpx
    if _async_client is None or _async_client.is_closed:
        _async_client = httpx.AsyncClient(timeout=30)
    return _async_client
try:
    from rapidfuzz import fuzz
except ImportError:
    import difflib
    class FakeFuzz:
        @staticmethod
        def ratio(s1: str, s2: str) -> float:
            return difflib.SequenceMatcher(None, s1, s2).ratio() * 100.0
    fuzz = FakeFuzz
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────

# Must be set via GROQ_API_KEY environment variable (no hardcoded fallback)
DEFAULT_GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# Common ATS-friendly section headers
ATS_SECTIONS = [
    "experience", "education", "skills", "certifications",
    "summary", "objective", "projects", "achievements",
    "professional experience", "work history", "technical skills",
    "core competencies", "professional summary", "qualifications",
]

# Industry-specific keywords weighted higher (Sam's Network Engineer domain)
KEYWORD_BOOST = {
    # Networking Core
    "network": 1.3, "networking": 1.3, "routing": 1.3, "switching": 1.3,
    "cisco": 1.3, "fortinet": 1.3, "mikrotik": 1.2, "ubiquiti": 1.1,
    "juniper": 1.2, "palo alto": 1.3, "checkpoint": 1.2, "sonicwall": 1.1,
    "firewall": 1.2, "vpn": 1.2, "vlan": 1.2, "ospf": 1.3, "bgp": 1.3,
    "mpls": 1.3, "dhcp": 1.1, "dns": 1.1, "nat": 1.1, "tcp/ip": 1.2,
    "lan": 1.1, "wan": 1.2,
    # Modern Networking (SD-WAN, SASE, ZTNA)
    "sd-wan": 1.4, "sase": 1.4, "ztna": 1.4, "zero trust": 1.3,
    "zero trust architecture": 1.4, "sdn": 1.3, "software defined networking": 1.3,
    "vxlan": 1.3, "evpn": 1.3, "segment routing": 1.3, "nfv": 1.2,
    "network function virtualization": 1.2, "silver peak": 1.3,
    "viptela": 1.3, "vmware nsx": 1.3, "cisco aci": 1.3,
    "meraki": 1.2, "aruba": 1.2, "ruckus": 1.1, "extremenetworks": 1.1,
    "riverbed": 1.2, "blue coat": 1.1, "zscaler": 1.3, "cloudflare": 1.2,
    "akamai": 1.2, "ipv6": 1.2, "multicast": 1.2, "qos": 1.2,
    "load balancing": 1.2, "f5": 1.2, "nginx": 1.1,
    # Protocols
    "eigrp": 1.2, "isis": 1.2, "is-is": 1.2, "stp": 1.1, "rstp": 1.1,
    "mstp": 1.1, "lacp": 1.1, "mlag": 1.1, "vrrp": 1.1, "hsrp": 1.1,
    "glbp": 1.1, "pim": 1.2, "igmp": 1.1, "snmp": 1.1, "netflow": 1.2,
    "sflow": 1.1, "ipfix": 1.1, "radius": 1.1, "tacacs": 1.1,
    "802.1x": 1.2, "macsec": 1.1, "dmvpn": 1.2, "getvpn": 1.2,
    "flexvpn": 1.2, "l2tp": 1.1, "gre": 1.1,
    # Security
    "security": 1.2, "cybersecurity": 1.2, "nse": 1.3, "fortigate": 1.3,
    "ips": 1.2, "ids": 1.2, "siem": 1.2, "soc": 1.2,
    "penetration testing": 1.2, "penetration test": 1.2, "ngfw": 1.3,
    "next generation firewall": 1.3, "waf": 1.2, "web application firewall": 1.2,
    "dlp": 1.2, "data loss prevention": 1.2, "endpoint security": 1.2,
    "edr": 1.2, "xdr": 1.2, "iam": 1.1, "pam": 1.1, "mfa": 1.1,
    "pki": 1.1, "tls": 1.1, "ssl": 1.1, "dmz": 1.2,
    "micro-segmentation": 1.3, "microsegmentation": 1.3,
    "nac": 1.2, "cisco ise": 1.3, "clearpass": 1.2, "aruba clearpass": 1.2,
    "threat intelligence": 1.2, "vulnerability management": 1.2,
    "incident response": 1.2, "forensics": 1.1, "soar": 1.2,
    # Cloud
    "cloud": 1.2, "aws": 1.2, "azure": 1.2, "gcp": 1.2,
    "aws vpc": 1.2, "direct connect": 1.2, "expressroute": 1.2,
    "azure expressroute": 1.2, "cloud interconnect": 1.2,
    "vmware": 1.2, "vsphere": 1.2, "hyper-v": 1.1,
    "openstack": 1.1, "oci": 1.1, "oracle cloud": 1.1,
    "cloud networking": 1.2, "cloud architecture": 1.2,
    # Automation / DevOps
    "automation": 1.2, "python": 1.2, "powershell": 1.1,
    "ansible": 1.3, "terraform": 1.3, "bash": 1.1, "shell scripting": 1.1,
    "git": 1.1, "github": 1.1, "gitlab": 1.1, "bitbucket": 1.1,
    "ci/cd": 1.2, "jenkins": 1.2, "gitlab ci": 1.2, "github actions": 1.2,
    "docker": 1.2, "kubernetes": 1.3, "k8s": 1.3, "istio": 1.2,
    "service mesh": 1.2, "netmiko": 1.2, "napalm": 1.2, "nornir": 1.2,
    "scrapli": 1.2, "pyats": 1.2, "genie": 1.2, "jinja2": 1.1,
    "yaml": 1.0, "json": 1.0, "rest api": 1.1, "postman": 1.0,
    "robot framework": 1.1, "saltstack": 1.1, "puppet": 1.1, "chef": 1.1,
    "netdevops": 1.3, "network automation": 1.3, "infrastructure as code": 1.3,
    "iac": 1.2, "devops": 1.2,
    # Monitoring / Observability
    "monitoring": 1.1, "observability": 1.1, "prtg": 1.1, "nagios": 1.1,
    "zabbix": 1.1, "solarwinds": 1.1, "wireshark": 1.1,
    "prometheus": 1.2, "grafana": 1.2, "elk": 1.2, "elasticsearch": 1.2,
    "logstash": 1.1, "kibana": 1.1, "splunk": 1.2, "datadog": 1.1,
    "new relic": 1.1, "librenms": 1.1, "observium": 1.0,
    "cacti": 1.0, "mrtg": 1.0, "smokeping": 1.0,
    "logicmonitor": 1.0, "appdynamics": 1.1, "dynatrace": 1.1,
    # Infrastructure
    "data center": 1.3, "datacenter": 1.3, "fiber optic": 1.1,
    "structured cabling": 1.0, "wireless": 1.1, "wifi": 1.1, "wi-fi": 1.1,
    "wifi 6": 1.2, "wifi 6e": 1.2, "campus network": 1.2,
    "branch office": 1.1, "colocation": 1.1, "disaster recovery": 1.2,
    "business continuity": 1.2, "rpo": 1.1, "rto": 1.1,
    "network segmentation": 1.2, "dci": 1.2, "data center interconnect": 1.2,
    # Certifications (higher boost)
    "ccna": 1.3, "ccnp": 1.3, "ccie": 1.4, "nse": 1.3,
    "nse 4": 1.3, "nse 5": 1.3, "nse 6": 1.3, "nse 7": 1.4,
    "mtcna": 1.2, "mtcre": 1.2, "mtcine": 1.3, "ubwa": 1.1,
    "fortinet nse": 1.3, "compTIA network": 1.2, "compTIA security": 1.2,
    "aws certified": 1.2, "azure network": 1.2, "itil": 1.1,
    "pcnsa": 1.2, "palo alto pcnsa": 1.2, "jncia": 1.2,
    "juniper jncia": 1.2, "devnet": 1.2, "cisco devnet": 1.2,
    "fcp": 1.2, "fortinet fcp": 1.2, "vcp-nv": 1.2, "cka": 1.2,
    "kubernetes administrator": 1.2,
    # Soft skills
    "leadership": 1.1, "team management": 1.1, "project management": 1.1,
    "troubleshooting": 1.1, "analytical": 1.0, "mentoring": 1.1,
    "vendor management": 1.1, "budget management": 1.1,
    "stakeholder management": 1.1, "cross-functional": 1.1,
    "strategic planning": 1.1, "team leadership": 1.1,
    # Industry domains
    "telecommunications": 1.1, "telecom": 1.1, "isp": 1.2,
    "managed services": 1.1, "mssp": 1.1, "enterprise": 1.0,
    "service provider": 1.1, "tier 2": 1.0, "tier 3": 1.1,
    "noc": 1.2, "network operations": 1.2, "soc analyst": 1.2,
    "network security": 1.3, "information security": 1.2,
    "infrastructure architect": 1.3, "solutions architect": 1.2,
    "network architect": 1.3, "network engineer": 1.2,
    "senior network engineer": 1.3, "principal engineer": 1.3,
    "network reliability": 1.2, "nre": 1.2,
    # Compliance / Standards
    "iso 27001": 1.2, "nist": 1.2, "gdpr": 1.1, "pci dss": 1.1,
    "hipaa": 1.1, "soc 2": 1.1, "compliance": 1.1,
    "audit": 1.0, "governance": 1.1,
    # ── 2025/2026 Modern Technology Keywords ─────────────────────────────────
    # AI/ML Infrastructure
    "llm": 1.4, "large language model": 1.4, "generative ai": 1.4,
    "rag": 1.3, "retrieval augmented generation": 1.3, "vector database": 1.3,
    "embeddings": 1.3, "openai": 1.3, "langchain": 1.3, "llama": 1.3,
    "hugging face": 1.2, "mlops": 1.3, "aiops": 1.3, "llmops": 1.3,
    "pinecone": 1.2, "weaviate": 1.2, "qdrant": 1.2, "chroma": 1.2,
    "semantic search": 1.2, "fine-tuning": 1.2, "prompt engineering": 1.3,
    # Platform Engineering & GitOps
    "platform engineering": 1.4, "internal developer platform": 1.3,
    "backstage": 1.3, "gitops": 1.3, "argocd": 1.3,
    "flux": 1.2, "crossplane": 1.3, "helm": 1.2, "kustomize": 1.2,
    "opentelemetry": 1.3, "otel": 1.2, "jaeger": 1.2,
    "cilium": 1.3, "ebpf": 1.4,
    "envoy": 1.2, "linkerd": 1.2, "consul": 1.2, "vault": 1.2,
    # Modern Cloud Security (CNAPP era)
    "cnapp": 1.4, "cloud native application protection": 1.3,
    "cspm": 1.3, "cloud security posture management": 1.3,
    "ciem": 1.3, "cwpp": 1.2, "cloud workload protection": 1.2,
    "devsecops": 1.3, "shift left security": 1.2,
    "supply chain security": 1.3, "sbom": 1.3, "software bill of materials": 1.3,
    "sigstore": 1.2, "cosign": 1.2, "slsa": 1.2,
    # Edge / Modern Networking
    "wasm": 1.3, "webassembly": 1.2, "edge computing": 1.3,
    "5g": 1.3, "private 5g": 1.3, "wifi 7": 1.3,
    "openran": 1.3, "open ran": 1.3, "o-ran": 1.3,
    # Multi-cloud & FinOps
    "multi-cloud": 1.3, "multicloud": 1.3, "hybrid cloud": 1.2,
    "finops": 1.3, "cloud cost optimization": 1.2,
    "aws transit gateway": 1.2, "azure virtual wan": 1.2,
    # SRE / Reliability
    "site reliability": 1.3, "sre": 1.3, "chaos engineering": 1.2,
    "slo": 1.2, "sli": 1.1, "error budget": 1.2,
    "distributed tracing": 1.2, "opentelemetry collector": 1.2,
}

STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'but', 'not', 'this',
    'that', 'from', 'as', 'we', 'our', 'your', 'its', 'their',
    'it', 'he', 'she', 'they', 'all', 'can', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'also', 'just', 'more',
    'very', 'than', 'then', 'each', 'some', 'any', 'both', 'such',
    'only', 'own', 'same', 'so', 'no', 'nor', 'too', 'if', 'about',
    'into', 'over', 'after', 'before', 'between', 'under', 'above',
    'below', 'up', 'down', 'out', 'off', 'near', 'every', 'good',
    'well', 'very', 'really', 'quite', 'much', 'while', 'during',
    'through', 'because', 'since', 'until', 'upon', 'per',
    'able', 'use', 'used', 'using', 'get', 'got', 'getting',
    'make', 'made', 'making', 'work', 'worked', 'working', 'works',
    'include', 'includes', 'including', 'included',
    'provide', 'provides', 'provided', 'providing',
    'support', 'supports', 'supported', 'supporting',
    'manage', 'manages', 'managed', 'managing',
    'responsible', 'responsibilities', 'duties', 'tasks',
    'year', 'years', 'experience', 'skill', 'skills',
    'knowledge', 'ability', 'strong', 'proven', 'excellent',
    'new', 'best', 'high', 'great', 'world', 'class',
    'first', 'last', 'next', 'other', 'additional', 'multiple',
    'various', 'different', 'wide', 'range', 'variety',
    'required', 'preferred', 'minimum', 'plus', 'including',
    'etc', 'e.g', 'i.e', 'desired', 'qualifications',
}


# ═══════════════════════════════════════════════════════════════════════════════
#  ATSMatcher — Core Algorithmic Engine
# ═══════════════════════════════════════════════════════════════════════════════

class ATSMatcher:
    """
    Analyzes resume vs job description using algorithmic keyword matching.

    Returns: match score %, missing keywords, skill gaps, ATS optimization tips.

    Usage:
        matcher = ATSMatcher()
        result = matcher.calculate_match(resume_text, jd_text)
        print(result["match_percent"])
    """

    def __init__(self, keyword_boost: Optional[Dict[str, float]] = None):
        self.keyword_boost = keyword_boost or KEYWORD_BOOST

    # ── Keyword Extraction ──────────────────────────────────────────────────

    def extract_keywords(self, text: str) -> Dict[str, int]:
        """Extract keywords with frequency from text. Supports unigrams + n-grams."""
        # Normalize
        text = NORMALIZE_RE.sub(' ', text.lower())

        words = text.split()

        # Build n-grams lazily using generators to save memory
        unigrams = words
        bigrams = (f"{words[i]} {words[i+1]}" for i in range(len(words) - 1))
        trigrams = (f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2))

        # Count frequencies
        freq: Dict[str, int] = {}

        # Chain generators/lists to avoid list concatenation memory overhead
        for term in itertools.chain(unigrams, bigrams, trigrams):
            if len(term) < 2 or term in STOP_WORDS or term.isdigit():
                continue
            freq[term] = freq.get(term, 0) + 1

        return freq

    # ── Core Match Engine ───────────────────────────────────────────────────

    def calculate_match(
        self,
        resume_text: str,
        job_description: str,
    ) -> Dict:
        """
        Calculate match between resume and job description.

        Returns a detailed breakdown dict with:
            - match_percent    : overall weighted score (0–100)
            - total_jd_keywords: unique keywords in JD
            - matched_keywords : count matched (exact + partial)
            - missing_keywords : count missing
            - top_missing      : list of top 20 missing keywords w/ importance
            - top_matched      : list of top 20 matched keywords w/ score
            - ats_tips         : actionable improvement suggestions
        """
        resume_kw = self.extract_keywords(resume_text)
        job_kw = self.extract_keywords(job_description)

        # Edge case: empty JD
        if not job_kw:
            return {
                "match_percent": 0,
                "missing_keywords": [],
                "matched_keywords": [],
                "total_jd_keywords": 0,
                "top_missing": [],
                "top_matched": [],
                "ats_tips": ["⚠️ Job description appears empty. Paste the full JD for accurate scoring."],
            }

        matched: Dict[str, Dict] = {}
        missing: Dict[str, Dict] = {}

        for kw, freq in sorted(job_kw.items(), key=lambda x: -x[1]):
            weight = self.keyword_boost.get(kw, 1.0)

            if kw in resume_kw:
                # Exact match
                matched[kw] = {
                    "jd_frequency": freq,
                    "resume_frequency": resume_kw[kw],
                    "weight": weight,
                    "weighted_score": min(1.0, resume_kw[kw] / max(freq, 1)) * weight,
                    "partial_match": None,
                }
            else:
                # Try partial / fuzzy match
                best_ratio = 0.0
                best_rk = None
                len_kw = len(kw)
                for rk in resume_kw:
                    len_rk = len(rk)
                    # Mathematical pruning: maximum possible fuzzy ratio is 2 * min(L1, L2) / (L1 + L2)
                    # If this upper bound is less than 0.7 or less than best_ratio, we can skip the heavy fuzz.ratio check
                    max_possible = (2.0 * min(len_kw, len_rk)) / (len_kw + len_rk)
                    if max_possible < 0.7 or max_possible < best_ratio:
                        continue
                        
                    # Allow fuzzy matching if length difference is small (e.g. typos, hyphens)
                    # or if one is a substring of the other (e.g. "vpn" in "vpns")
                    if abs(len_kw - len_rk) <= 4 or kw in rk or rk in kw:
                        ratio = fuzz.ratio(kw, rk) / 100.0
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_rk = rk
                            if best_ratio == 1.0:
                                break

                if best_ratio >= 0.7:
                    matched[kw] = {
                        "jd_frequency": freq,
                        "resume_frequency": resume_kw.get(best_rk, 1),
                        "weight": weight,
                        "weighted_score": best_ratio * weight,
                        "partial_match": best_rk,
                    }
                else:
                    missing[kw] = {
                        "jd_frequency": freq,
                        "weight": weight,
                    }

        # Calculate mathematically sound weighted score
        total_earned_weight = 0.0
        total_possible_weight = 0.0

        for kw, info in matched.items():
            max_kw_weight = info["weight"] * info["jd_frequency"]
            total_possible_weight += max_kw_weight
            total_earned_weight += info["weighted_score"] * info["jd_frequency"]

        for kw, info in missing.items():
            max_kw_weight = info["weight"] * info["jd_frequency"]
            total_possible_weight += max_kw_weight

        match_percent = round(
            (total_earned_weight / max(total_possible_weight, 1.0)) * 100, 1
        )

        # Sort missing by importance (descending)
        missing_sorted = sorted(
            missing.items(),
            key=lambda x: x[1]["weight"] * x[1]["jd_frequency"],
            reverse=True,
        )

        # Sort matched by weighted_score (descending)
        matched_sorted = sorted(
            matched.items(),
            key=lambda x: -x[1]["weighted_score"],
        )

        return {
            "match_percent": match_percent,
            "total_jd_keywords": len(job_kw),
            "matched_keywords_count": len(matched),
            "missing_keywords_count": len(missing),
            "top_missing": [
                {
                    "keyword": kw,
                    "importance": round(
                        info["weight"] * info["jd_frequency"], 2
                    ),
                }
                for kw, info in missing_sorted[:20]
            ],
            "top_matched": [
                {
                    "keyword": kw,
                    "score": round(info["weighted_score"], 2),
                    "partial": info.get("partial_match"),
                }
                for kw, info in matched_sorted[:20]
            ],
            "all_missing_keywords": [kw for kw, _ in missing_sorted],
            "all_matched_keywords": [kw for kw, _ in matched_sorted],
            "ats_tips": self._generate_tips(
                match_percent, missing_sorted[:5], len(job_kw), len(matched)
            ),
            "keyword_breakdown": {
                "exact_matches": sum(
                    1 for m in matched.values() if not m.get("partial_match")
                ),
                "partial_matches": sum(
                    1 for m in matched.values() if m.get("partial_match")
                ),
            },
        }

    # ── Tips Generator ─────────────────────────────────────────────────────

    def _generate_tips(
        self,
        match_percent: float,
        top_missing: List[Tuple[str, Dict]],
        total_jd: int,
        total_matched: int,
    ) -> List[str]:
        """Generate actionable ATS optimization tips."""
        tips = []

        # Severity banner
        if match_percent < 20:
            tips.append(
                "🔴 Critical: Your resume misses most JD keywords. "
                "Major overhaul required — tailor each section."
            )
        elif match_percent < 35:
            tips.append(
                "🚨 Very low match. Add specific technical keywords "
                "and rephrase bullet points to mirror the JD."
            )
        elif match_percent < 50:
            tips.append(
                "⚠️ Low match. Focus on adding the missing keywords "
                "listed below to improve your score significantly."
            )
        elif match_percent < 65:
            tips.append(
                "🟡 Moderate match. Good foundation. Fill skill gaps "
                "and strengthen weak areas to reach 70%+."
            )
        elif match_percent < 80:
            tips.append(
                "🟢 Solid match! Minor tweaks — add the missing keywords "
                "and you'll easily hit 80%+."
            )
        elif match_percent < 90:
            tips.append(
                "💪 Strong match! Very competitive. Fine-tune with "
                "the last few missing terms to push past 90%."
            )
        else:
            tips.append(
                "✅ Excellent match! Your resume is well-optimized "
                "for this role. Send it confidently."
            )

        # Missing keyword tips
        if top_missing:
            keywords_5 = [kw for kw, _ in top_missing[:5]]
            tips.append(
                f"📌 Add these top keywords to your resume: "
                f"{', '.join(keywords_5)}"
            )
            tips.append(
                f"💡 Prioritize adding experience with: "
                f"'{top_missing[0][0]}' — it carries the most weight."
            )

        # Ratio tip
        ratio = total_matched / max(total_jd, 1)
        if ratio < 0.3:
            tips.append(
                "📊 Your resume covers fewer than 30% of JD keywords. "
                "Consider rewriting your skills section to match "
                "the exact terminology used in the job posting."
            )
        elif ratio < 0.5:
            tips.append(
                "📊 Keyword coverage is adequate (30-50%). "
                "Try adding a 'Core Competencies' section with "
                "JD-aligned terms for an instant boost."
            )

        # General ATS advice
        tips.append(
            "🧠 ATS Tip: Use <b>standard section headers</b> "
            "(Experience, Education, Skills) — avoid creative titles "
            "that parsers may not recognize."
        )
        tips.append(
            "📄 Use a clean, single-column layout. Avoid tables, "
            "images, charts, and text boxes — they confuse ATS parsers."
        )

        return tips

    # ── Utility ─────────────────────────────────────────────────────────────

    def section_relevance(self, resume_sections: Dict[str, str]) -> Dict[str, float]:
        """Score relevance of each resume section against common ATS sections."""
        scores = {}
        for section in ATS_SECTIONS:
            for rs, content in resume_sections.items():
                if section in rs.lower():
                    # Score based on keyword density
                    kw = self.extract_keywords(content)
                    scores[rs] = len(kw)
                    break
        return scores


# ═══════════════════════════════════════════════════════════════════════════════
#  Groq AI Enhanced Analysis
# ═══════════════════════════════════════════════════════════════════════════════

_llm_pool = None

def _get_llm_pool():
    global _llm_pool
    if _llm_pool is None:
        try:
            from core.llm_provider_pool import LLMProviderPool
            _llm_pool = LLMProviderPool().initialize()
        except Exception as e:
            logger.warning(f"Failed to initialize LLMProviderPool in ats_matcher: {e}")
    return _llm_pool


def _run_async(coro):
    """Run an async coroutine from a synchronous context safely."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def analyze_with_groq(
    resume_text: str,
    jd_text: str,
    groq_key: str = DEFAULT_GROQ_KEY,
    model: str = "mixtral-8x7b-32768",
) -> Dict:
    """
    Use LLM Provider Pool for deep ATS analysis. Enhances keyword matching with
    semantic understanding, format critique, and nuanced scoring.
    Falls back to legacy direct Groq call if pool fails.
    """
    return _run_async(analyze_with_groq_async(resume_text, jd_text, groq_key, model))


async def analyze_with_groq_async(
    resume_text: str,
    jd_text: str,
    groq_key: str = DEFAULT_GROQ_KEY,
    model: str = "mixtral-8x7b-32768",
) -> Dict:
    """Async version of analyze_with_groq using LLMProviderPool with legacy Groq fallback."""
    prompt = f"""You are an ATS (Applicant Tracking System) expert. Analyze this resume vs job description.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{jd_text[:3000]}

Return JSON ONLY (no markdown, no code fences, no extra text):
{{
  "match_percent": <0-100>,
  "missing_skills": ["skill1", "skill2"],
  "matched_skills": ["skill1", "skill2"],
  "ats_score": <0-100>,
  "improvement_tips": ["tip1", "tip2"],
  "format_issues": ["issue1"]
}}
"""
    # 1. Try rotating LLM Provider Pool first
    pool = _get_llm_pool()
    if pool:
        try:
            content = await pool.complete(
                system_prompt="You are an ATS expert. Answer in JSON only.",
                user_prompt=prompt,
                temperature=0.1,
                max_tokens=1000
            )
            if content:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as pool_err:
            logger.warning(f"[ATS-Pool] Pool completion failed: {pool_err}. Falling back to direct Groq...")

    # 2. Legacy Fallback: Direct Groq API call
    if groq_key:
        try:
            client = _get_async_client()
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1000,
                },
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            else:
                logger.warning(f"[ATS-Groq] API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"[ATS-Groq] Async error: {e}")

    return {}


# ═══════════════════════════════════════════════════════════════════════════════
#  Combined Analysis (Algorithmic + Groq)
# ═══════════════════════════════════════════════════════════════════════════════

def full_ats_analysis(
    resume_text: str,
    job_description: str,
    use_groq: bool = True,
    groq_key: str = DEFAULT_GROQ_KEY,
) -> Dict:
    """
    Run both algorithmic (ATSMatcher) and Groq AI analysis, then merge results.

    This gives Sam the best of both worlds:
    - Fast, deterministic keyword matching (no API cost)
    - Deep semantic analysis from Groq (when enabled)

    Args:
        resume_text: Full resume text
        job_description: Full job description
        use_groq: Whether to include Groq AI analysis
        groq_key: Groq API key

    Returns:
        Merged dict with both algorithmic + AI results
    """
    # Algorithmic match (always runs — zero cost)
    matcher = ATSMatcher()
    algo_result = matcher.calculate_match(resume_text, job_description)

    result = {
        "algorithmic": algo_result,
        "ai_analysis": {},
        "combined_score": algo_result["match_percent"],
        "source": "algorithmic",
    }

    # Groq enhancement
    if use_groq and groq_key:
        ai_result = analyze_with_groq(resume_text, job_description, groq_key)
        if ai_result:
            result["ai_analysis"] = ai_result
            # Combine: average algorithmic + AI (weighted 60/40)
            ai_match = ai_result.get("match_percent", 0)
            combined = round(algo_result["match_percent"] * 0.6 + ai_match * 0.4, 1)
            result["combined_score"] = combined
            result["source"] = "hybrid"

    # Deduplicate missing keywords
    missing_set: set = set(algo_result.get("all_missing_keywords", []))
    missing_set.update(ai_result.get("missing_skills", []))
    result["all_missing_deduped"] = sorted(missing_set)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  Telegram Bot Command Hook
# ═══════════════════════════════════════════════════════════════════════════════

def format_ats_for_telegram(result: Dict) -> str:
    """
    Format ATS match results into a Telegram-friendly message.
    """
    algo = result.get("algorithmic", {})
    combined = result.get("combined_score", 0)
    source = result.get("source", "algorithmic")

    lines = ["<b>📊 ATS Resume Match Score</b>", ""]

    # Score with emoji
    score = combined
    if score >= 80:
        score_emoji = "🟢"
    elif score >= 60:
        score_emoji = "🟡"
    elif score >= 40:
        score_emoji = "🟠"
    else:
        score_emoji = "🔴"

    lines.append(f"{score_emoji} <b>Match Score: {score}%</b>")
    lines.append(f"   Source: {source.upper()}")
    lines.append("")

    # Breakdown
    lines.append("<b>📋 Breakdown:</b>")
    lines.append(f"   • JD Keywords: {algo.get('total_jd_keywords', 0)}")
    lines.append(f"   • Matched: {algo.get('matched_keywords_count', 0)}")
    lines.append(f"   • Missing: {algo.get('missing_keywords_count', 0)}")
    lines.append("")

    # Top missing keywords
    top_missing = algo.get("top_missing", [])
    if top_missing:
        lines.append("<b>❗ Top Missing Keywords:</b>")
        for kw_info in top_missing[:8]:
            lines.append(
                f"   • <code>{kw_info['keyword']}</code> "
                f"(importance: {kw_info['importance']})"
            )
        lines.append("")

    # ATS Tips
    tips = algo.get("ats_tips", [])
    if tips:
        lines.append("<b>💡 Optimization Tips:</b>")
        for tip in tips[:5]:
            lines.append(f"   • {tip}")
        lines.append("")

    lines.append("───")
    lines.append("🤖 <i>Optimize your resume and re-run to improve your score.</i>")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  FastAPI / Flask Integration Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def api_ats_score(
    resume_text: str,
    job_description: str,
    use_groq: bool = True,
    groq_key: str = DEFAULT_GROQ_KEY,
) -> Dict:
    """
    API-friendly wrapper for full_ats_analysis.
    Designed to be called directly from FastAPI or Flask endpoints.

    Example FastAPI usage:
        @app.post("/api/ats-score")
        async def ats_score(payload: ATSRequest):
            return api_ats_score(payload.resume, payload.jd)

    Returns serializable dict (no Python-specific objects).
    """
    return full_ats_analysis(
        resume_text=resume_text,
        job_description=job_description,
        use_groq=use_groq,
        groq_key=groq_key,
    )


def parse_resume_from_file(filepath: str) -> str:
    """Read resume text from a file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════════════════════
#  Quick Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_resume = """
    Sam Salameh — Senior Network Engineer
    Skills: Cisco routing/switching, Fortinet Firewalls, MikroTik, Ubiquiti,
    Python automation, Linux administration, AWS Cloud, VPN, VLAN, OSPF, BGP.
    Certifications: CCNA, Fortinet NSE, MikroTik MTCNA, Ubiquiti UBWA.
    """

    sample_jd = """
    We need a Senior Network Engineer with strong Cisco and Fortinet experience.
    Must have CCNA or equivalent. Cloud experience (AWS/Azure) preferred.
    Knowledge of SD-WAN, MPLS, and automation tools (Ansible/Terraform) is a plus.
    """

    matcher = ATSMatcher()
    result = matcher.calculate_match(sample_resume, sample_jd)
    print(f"Match Score: {result['match_percent']}%")
    print(f"Missing: {result['missing_keywords_count']} keywords")
    for kw_info in result["top_missing"][:5]:
        print(f"  ✗ {kw_info['keyword']} (imp: {kw_info['importance']})")

    print("\n── Telegram Preview ──")
    print(format_ats_for_telegram({"algorithmic": result, "combined_score": result["match_percent"], "source": "algorithmic"}))
