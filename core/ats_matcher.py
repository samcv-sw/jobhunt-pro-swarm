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

import hashlib
import itertools
import json
import logging
import math
import os
import re
from collections import defaultdict

import config

# Standardized taxonomy set of tech keywords
TECH_TAXONOMY = {skill.lower() for skill in config.SKILLS}
# Add additional standard tech keywords to support general technology and test cases
_additional = {
    # Programming languages and systems
    "python", "java", "c++", "c", "c#", "golang", "go", "javascript", "typescript", "ruby", "php", "html", "css", "sql", "nosql", "rust",
    # Core networking concepts
    "vpn", "vpns", "protocol", "protocols", "routing", "switching", "router", "switch", "cisco", "juniper", "fortinet", "mikrotik", "ubiquiti",
    # Roles and general tech terms
    "developer", "development", "engineer", "engineering", "architect", "administrator", "administration", "analyst", "specialist", "consultant",
    "cloud", "azure", "aws", "kubernetes", "k8s", "docker", "containers", "ci/cd", "cicd", "automation", "security", "infrastructure", "system", "systems",
    "monitoring", "database", "databases", "programming", "experience", "active directory", "virtualization", "hypervisor", "firewall", "firewalls",
    "network", "networking", "noc", "soc", "telecom", "telecommunications", "sre"
}
TECH_TAXONOMY.update(_additional)

# Synonym map
SYNONYM_MAP = {
    "k8s": "kubernetes",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "azure": "microsoft azure",
    "docker": "containers",
    "cicd": "ci/cd",
    "ci/cd": "continuous integration continuous deployment",
    "netdevops": "network automation",
    "prometheus": "monitoring",
    "grafana": "observability",
    "elk": "elasticsearch logstash kibana",
    "ipsec": "vpn",
    "vpns": "vpn",
    "tg": "telegram",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "restful": "rest",
    "sqlserver": "mssql"
}

def get_canonical_term(term: str) -> str:
    t = term.strip().lower()
    return SYNONYM_MAP.get(t, t)

# Globally precompiled regex for normalization
NORMALIZE_RE = re.compile(r"[^\w\s\-+#./]")

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
    "experience",
    "education",
    "skills",
    "certifications",
    "summary",
    "objective",
    "projects",
    "achievements",
    "professional experience",
    "work history",
    "technical skills",
    "core competencies",
    "professional summary",
    "qualifications",
]

# Industry-specific keywords weighted higher (Sam's Network Engineer domain)
KEYWORD_BOOST = {
    # Networking Core
    "network": 1.3,
    "networking": 1.3,
    "routing": 1.3,
    "switching": 1.3,
    "cisco": 1.3,
    "fortinet": 1.3,
    "mikrotik": 1.2,
    "ubiquiti": 1.1,
    "juniper": 1.2,
    "palo alto": 1.3,
    "checkpoint": 1.2,
    "sonicwall": 1.1,
    "firewall": 1.2,
    "vpn": 1.2,
    "vlan": 1.2,
    "ospf": 1.3,
    "bgp": 1.3,
    "mpls": 1.3,
    "dhcp": 1.1,
    "dns": 1.1,
    "nat": 1.1,
    "tcp/ip": 1.2,
    "lan": 1.1,
    "wan": 1.2,
    # Modern Networking (SD-WAN, SASE, ZTNA)
    "sd-wan": 1.4,
    "sase": 1.4,
    "ztna": 1.4,
    "zero trust": 1.3,
    "zero trust architecture": 1.4,
    "sdn": 1.3,
    "software defined networking": 1.3,
    "vxlan": 1.3,
    "evpn": 1.3,
    "segment routing": 1.3,
    "nfv": 1.2,
    "network function virtualization": 1.2,
    "silver peak": 1.3,
    "viptela": 1.3,
    "vmware nsx": 1.3,
    "cisco aci": 1.3,
    "meraki": 1.2,
    "aruba": 1.2,
    "ruckus": 1.1,
    "extremenetworks": 1.1,
    "riverbed": 1.2,
    "blue coat": 1.1,
    "zscaler": 1.3,
    "cloudflare": 1.2,
    "akamai": 1.2,
    "ipv6": 1.2,
    "multicast": 1.2,
    "qos": 1.2,
    "load balancing": 1.2,
    "f5": 1.2,
    "nginx": 1.1,
    # Protocols
    "eigrp": 1.2,
    "isis": 1.2,
    "is-is": 1.2,
    "stp": 1.1,
    "rstp": 1.1,
    "mstp": 1.1,
    "lacp": 1.1,
    "mlag": 1.1,
    "vrrp": 1.1,
    "hsrp": 1.1,
    "glbp": 1.1,
    "pim": 1.2,
    "igmp": 1.1,
    "snmp": 1.1,
    "netflow": 1.2,
    "sflow": 1.1,
    "ipfix": 1.1,
    "radius": 1.1,
    "tacacs": 1.1,
    "802.1x": 1.2,
    "macsec": 1.1,
    "dmvpn": 1.2,
    "getvpn": 1.2,
    "flexvpn": 1.2,
    "l2tp": 1.1,
    "gre": 1.1,
    # Security
    "security": 1.2,
    "cybersecurity": 1.2,
    "nse": 1.3,
    "fortigate": 1.3,
    "ips": 1.2,
    "ids": 1.2,
    "siem": 1.2,
    "soc": 1.2,
    "penetration testing": 1.2,
    "penetration test": 1.2,
    "ngfw": 1.3,
    "next generation firewall": 1.3,
    "waf": 1.2,
    "web application firewall": 1.2,
    "dlp": 1.2,
    "data loss prevention": 1.2,
    "endpoint security": 1.2,
    "edr": 1.2,
    "xdr": 1.2,
    "iam": 1.1,
    "pam": 1.1,
    "mfa": 1.1,
    "pki": 1.1,
    "tls": 1.1,
    "ssl": 1.1,
    "dmz": 1.2,
    "micro-segmentation": 1.3,
    "microsegmentation": 1.3,
    "nac": 1.2,
    "cisco ise": 1.3,
    "clearpass": 1.2,
    "aruba clearpass": 1.2,
    "threat intelligence": 1.2,
    "vulnerability management": 1.2,
    "incident response": 1.2,
    "forensics": 1.1,
    "soar": 1.2,
    # Cloud
    "cloud": 1.2,
    "aws": 1.2,
    "azure": 1.2,
    "gcp": 1.2,
    "aws vpc": 1.2,
    "direct connect": 1.2,
    "expressroute": 1.2,
    "azure expressroute": 1.2,
    "cloud interconnect": 1.2,
    "vmware": 1.2,
    "vsphere": 1.2,
    "hyper-v": 1.1,
    "openstack": 1.1,
    "oci": 1.1,
    "oracle cloud": 1.1,
    "cloud networking": 1.2,
    "cloud architecture": 1.2,
    # Automation / DevOps
    "automation": 1.2,
    "python": 1.2,
    "powershell": 1.1,
    "ansible": 1.3,
    "terraform": 1.3,
    "bash": 1.1,
    "shell scripting": 1.1,
    "git": 1.1,
    "github": 1.1,
    "gitlab": 1.1,
    "bitbucket": 1.1,
    "ci/cd": 1.2,
    "jenkins": 1.2,
    "gitlab ci": 1.2,
    "github actions": 1.2,
    "docker": 1.2,
    "kubernetes": 1.3,
    "k8s": 1.3,
    "istio": 1.2,
    "service mesh": 1.2,
    "netmiko": 1.2,
    "napalm": 1.2,
    "nornir": 1.2,
    "scrapli": 1.2,
    "pyats": 1.2,
    "genie": 1.2,
    "jinja2": 1.1,
    "yaml": 1.0,
    "json": 1.0,
    "rest api": 1.1,
    "postman": 1.0,
    "robot framework": 1.1,
    "saltstack": 1.1,
    "puppet": 1.1,
    "chef": 1.1,
    "netdevops": 1.3,
    "network automation": 1.3,
    "infrastructure as code": 1.3,
    "iac": 1.2,
    "devops": 1.2,
    # Monitoring / Observability
    "monitoring": 1.1,
    "observability": 1.1,
    "prtg": 1.1,
    "nagios": 1.1,
    "zabbix": 1.1,
    "solarwinds": 1.1,
    "wireshark": 1.1,
    "prometheus": 1.2,
    "grafana": 1.2,
    "elk": 1.2,
    "elasticsearch": 1.2,
    "logstash": 1.1,
    "kibana": 1.1,
    "splunk": 1.2,
    "datadog": 1.1,
    "new relic": 1.1,
    "librenms": 1.1,
    "observium": 1.0,
    "cacti": 1.0,
    "mrtg": 1.0,
    "smokeping": 1.0,
    "logicmonitor": 1.0,
    "appdynamics": 1.1,
    "dynatrace": 1.1,
    # Infrastructure
    "data center": 1.3,
    "datacenter": 1.3,
    "fiber optic": 1.1,
    "structured cabling": 1.0,
    "wireless": 1.1,
    "wifi": 1.1,
    "wi-fi": 1.1,
    "wifi 6": 1.2,
    "wifi 6e": 1.2,
    "campus network": 1.2,
    "branch office": 1.1,
    "colocation": 1.1,
    "disaster recovery": 1.2,
    "business continuity": 1.2,
    "rpo": 1.1,
    "rto": 1.1,
    "network segmentation": 1.2,
    "dci": 1.2,
    "data center interconnect": 1.2,
    # Certifications (higher boost)
    "ccna": 1.3,
    "ccnp": 1.3,
    "ccie": 1.4,
    "nse 4": 1.3,
    "nse 5": 1.3,
    "nse 6": 1.3,
    "nse 7": 1.4,
    "mtcna": 1.2,
    "mtcre": 1.2,
    "mtcine": 1.3,
    "ubwa": 1.1,
    "fortinet nse": 1.3,
    "compTIA network": 1.2,
    "compTIA security": 1.2,
    "aws certified": 1.2,
    "azure network": 1.2,
    "itil": 1.1,
    "pcnsa": 1.2,
    "palo alto pcnsa": 1.2,
    "jncia": 1.2,
    "juniper jncia": 1.2,
    "devnet": 1.2,
    "cisco devnet": 1.2,
    "fcp": 1.2,
    "fortinet fcp": 1.2,
    "vcp-nv": 1.2,
    "cka": 1.2,
    "kubernetes administrator": 1.2,
    # Soft skills
    "leadership": 1.1,
    "team management": 1.1,
    "project management": 1.1,
    "troubleshooting": 1.1,
    "analytical": 1.0,
    "mentoring": 1.1,
    "vendor management": 1.1,
    "budget management": 1.1,
    "stakeholder management": 1.1,
    "cross-functional": 1.1,
    "strategic planning": 1.1,
    "team leadership": 1.1,
    # Industry domains
    "telecommunications": 1.1,
    "telecom": 1.1,
    "isp": 1.2,
    "managed services": 1.1,
    "mssp": 1.1,
    "enterprise": 1.0,
    "service provider": 1.1,
    "tier 2": 1.0,
    "tier 3": 1.1,
    "noc": 1.2,
    "network operations": 1.2,
    "soc analyst": 1.2,
    "network security": 1.3,
    "information security": 1.2,
    "infrastructure architect": 1.3,
    "solutions architect": 1.2,
    "network architect": 1.3,
    "network engineer": 1.2,
    "senior network engineer": 1.3,
    "principal engineer": 1.3,
    "network reliability": 1.2,
    "nre": 1.2,
    # Compliance / Standards
    "iso 27001": 1.2,
    "nist": 1.2,
    "gdpr": 1.1,
    "pci dss": 1.1,
    "hipaa": 1.1,
    "soc 2": 1.1,
    "compliance": 1.1,
    "audit": 1.0,
    "governance": 1.1,
    # ── 2025/2026 Modern Technology Keywords ─────────────────────────────────
    # AI/ML Infrastructure
    "llm": 1.4,
    "large language model": 1.4,
    "generative ai": 1.4,
    "rag": 1.3,
    "retrieval augmented generation": 1.3,
    "vector database": 1.3,
    "embeddings": 1.3,
    "openai": 1.3,
    "langchain": 1.3,
    "llama": 1.3,
    "hugging face": 1.2,
    "mlops": 1.3,
    "aiops": 1.3,
    "llmops": 1.3,
    "pinecone": 1.2,
    "weaviate": 1.2,
    "qdrant": 1.2,
    "chroma": 1.2,
    "semantic search": 1.2,
    "fine-tuning": 1.2,
    "prompt engineering": 1.3,
    # Platform Engineering & GitOps
    "platform engineering": 1.4,
    "internal developer platform": 1.3,
    "backstage": 1.3,
    "gitops": 1.3,
    "argocd": 1.3,
    "flux": 1.2,
    "crossplane": 1.3,
    "helm": 1.2,
    "kustomize": 1.2,
    "opentelemetry": 1.3,
    "otel": 1.2,
    "jaeger": 1.2,
    "cilium": 1.3,
    "ebpf": 1.4,
    "envoy": 1.2,
    "linkerd": 1.2,
    "consul": 1.2,
    "vault": 1.2,
    # Modern Cloud Security (CNAPP era)
    "cnapp": 1.4,
    "cloud native application protection": 1.3,
    "cspm": 1.3,
    "cloud security posture management": 1.3,
    "ciem": 1.3,
    "cwpp": 1.2,
    "cloud workload protection": 1.2,
    "devsecops": 1.3,
    "shift left security": 1.2,
    "supply chain security": 1.3,
    "sbom": 1.3,
    "software bill of materials": 1.3,
    "sigstore": 1.2,
    "cosign": 1.2,
    "slsa": 1.2,
    # Edge / Modern Networking
    "wasm": 1.3,
    "webassembly": 1.2,
    "edge computing": 1.3,
    "5g": 1.3,
    "private 5g": 1.3,
    "wifi 7": 1.3,
    "openran": 1.3,
    "open ran": 1.3,
    "o-ran": 1.3,
    # Multi-cloud & FinOps
    "multi-cloud": 1.3,
    "multicloud": 1.3,
    "hybrid cloud": 1.2,
    "finops": 1.3,
    "cloud cost optimization": 1.2,
    "aws transit gateway": 1.2,
    "azure virtual wan": 1.2,
    # SRE / Reliability
    "site reliability": 1.3,
    "sre": 1.3,
    "chaos engineering": 1.2,
    "slo": 1.2,
    "sli": 1.1,
    "error budget": 1.2,
    "distributed tracing": 1.2,
    "opentelemetry collector": 1.2,
}

STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "but",
    "not",
    "this",
    "that",
    "from",
    "as",
    "we",
    "our",
    "your",
    "its",
    "their",
    "it",
    "he",
    "she",
    "they",
    "all",
    "can",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "also",
    "just",
    "more",
    "very",
    "than",
    "then",
    "each",
    "some",
    "any",
    "both",
    "such",
    "only",
    "own",
    "same",
    "so",
    "no",
    "nor",
    "too",
    "if",
    "about",
    "into",
    "over",
    "after",
    "before",
    "between",
    "under",
    "above",
    "below",
    "up",
    "down",
    "out",
    "off",
    "near",
    "every",
    "good",
    "well",
    "really",
    "quite",
    "much",
    "while",
    "during",
    "through",
    "because",
    "since",
    "until",
    "upon",
    "per",
    "able",
    "use",
    "used",
    "using",
    "get",
    "got",
    "getting",
    "make",
    "made",
    "making",
    "work",
    "worked",
    "working",
    "works",
    "include",
    "includes",
    "including",
    "included",
    "provide",
    "provides",
    "provided",
    "providing",
    "support",
    "supports",
    "supported",
    "supporting",
    "manage",
    "manages",
    "managed",
    "managing",
    "responsible",
    "responsibilities",
    "duties",
    "tasks",
    "year",
    "years",
    "experience",
    "skill",
    "skills",
    "knowledge",
    "ability",
    "strong",
    "proven",
    "excellent",
    "new",
    "best",
    "high",
    "great",
    "world",
    "class",
    "first",
    "last",
    "next",
    "other",
    "additional",
    "multiple",
    "various",
    "different",
    "wide",
    "range",
    "variety",
    "required",
    "preferred",
    "minimum",
    "plus",
    "etc",
    "e.g",
    "i.e",
    "desired",
    "qualifications",
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
        logger.debug(result["match_percent"])
    """

    def __init__(self, keyword_boost: dict[str, float] | None = None):
        self.keyword_boost = keyword_boost or KEYWORD_BOOST

    # ── Keyword Extraction ──────────────────────────────────────────────────

    def extract_keywords(self, text: str) -> dict[str, int]:
        """Extract keywords with frequency from text. Supports unigrams + n-grams."""
        # Normalize
        text = NORMALIZE_RE.sub(" ", text.lower())

        words = text.split()

        # Build n-grams lazily using generators to save memory
        unigrams = words
        bigrams = (f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1))
        trigrams = (
            f"{words[i]} {words[i + 1]} {words[i + 2]}" for i in range(len(words) - 2)
        )

        # Count frequencies
        freq: dict[str, int] = {}

        # Chain generators/lists to avoid list concatenation memory overhead
        for term in itertools.chain(unigrams, bigrams, trigrams):
            if len(term) < 2 or term in STOP_WORDS or term.isdigit():
                continue

            # Standardized taxonomy filtering:
            # Term itself or any of its constituent words must be in the tech taxonomy
            words_in_term = term.split()
            is_tech = term in TECH_TAXONOMY or any(w in TECH_TAXONOMY for w in words_in_term)
            if not is_tech:
                continue

            freq[term] = freq.get(term, 0) + 1

        return freq

    # ── Core Match Engine ───────────────────────────────────────────────────

    def _calculate_idf_weights(
        self,
        job_kw: dict[str, int],
        job_description: str,
    ) -> dict[str, float]:
        """
        Calculate dynamic IDF weights for all job description keywords.

        Args:
            job_kw: Dict of job description keywords and their frequencies.
            job_description: The job description text.

        Returns:
            A dictionary mapping keywords to their IDF weights.
        """
        sentences = [s.strip().lower() for s in re.split(r'[.!?\n]', job_description) if s.strip()]
        N = len(sentences)
        idf_weights = {}
        for kw in job_kw:
            if N > 1:
                # Count how many sentences contain kw
                d_t = sum(1 for s in sentences if kw in s)
                # ln(1 + N / (1 + d_t))
                val = math.log(1.0 + N / (1.0 + d_t))
                # Scale it so the boost is between 1.0 and 2.0
                weight = 1.0 + (val / math.log(N + 1)) * 0.5
            else:
                weight = 1.0
            idf_weights[kw] = round(weight, 3)
        return idf_weights

    def _match_keywords(
        self,
        resume_kw: dict[str, int],
        job_kw: dict[str, int],
        idf_weights: dict[str, float],
    ) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Determine matched and missing keywords by checking exact, synonym, and fuzzy matches.

        Args:
            resume_kw: Dict of resume keywords and frequencies.
            job_kw: Dict of job keywords and frequencies.
            idf_weights: Dict of dynamic IDF weights for job keywords.

        Returns:
            A tuple of (matched_dict, missing_dict).
        """
        matched: dict[str, dict] = {}
        missing: dict[str, dict] = {}

        # Optimize: initial letter hash map of resume keywords
        resume_by_letter = defaultdict(list)
        for rk in resume_kw:
            if rk:
                resume_by_letter[rk[0]].append(rk)

        for kw, freq in sorted(job_kw.items(), key=lambda x: -x[1]):
            # Use dynamic IDF weight
            weight = idf_weights.get(kw, 1.0)

            # Synonym mapping check
            canonical_kw = get_canonical_term(kw)
            exact_rk = None
            for rk in resume_kw:
                if rk == kw or get_canonical_term(rk) == canonical_kw:
                    exact_rk = rk
                    break

            if exact_rk:
                # Exact or Synonym match
                matched[kw] = {
                    "jd_frequency": freq,
                    "resume_frequency": resume_kw[exact_rk],
                    "weight": weight,
                    "weighted_score": min(1.0, resume_kw[exact_rk] / max(freq, 1)) * weight,
                    "partial_match": None if exact_rk == kw else exact_rk,
                }
            else:
                # Try partial / fuzzy match
                best_ratio = 0.0
                best_rk = None
                len_kw = len(kw)

                # Retrieve candidates starting with the same character
                first_char = kw[0] if kw else ""
                candidates = resume_by_letter.get(first_char, [])

                # Fallback to check other keys with substring match or close length
                additional = [
                    rk for rk in resume_kw
                    if rk[0] != first_char and (abs(len(rk) - len_kw) <= 2 or kw in rk or rk in kw)
                ]
                candidates = candidates + additional

                for rk in candidates:
                    len_rk = len(rk)

                    # Length check prune
                    if abs(len_kw - len_rk) > 4:
                        continue

                    # Mathematical pruning: maximum possible fuzzy ratio is 2 * min(L1, L2) / (L1 + L2)
                    max_possible = (2.0 * min(len_kw, len_rk)) / (len_kw + len_rk)
                    if max_possible < 0.7 or max_possible < best_ratio:
                        continue

                    # Allow fuzzy matching if length difference is small or substring
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
        return matched, missing

    def calculate_arabic_match(self, resume_text: str, job_description: str) -> dict:
        """
        IMP-183: AraBERT Arabic NLP job-CV matching.
        Calculates semantic similarity between Arabic resumes and JDs using aubmindlab/bert-base-arabertv02 via Hugging Face.
        Falls back to specialized Arabic TF-IDF if API is unavailable.
        """
        # Extract Arabic words by splitting and keeping arabic chars
        arabic_words = re.findall(r'[\u0600-\u06FF]+', job_description)
        unique_jd_kws = list(set(arabic_words))
        
        # Try Hugging Face Inference API
        hf_token = os.getenv("HF_API_KEY")
        score = None
        if hf_token:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {hf_token}"}
                response = httpx.post(
                    "https://api-inference.huggingface.co/models/sentence-transformers/laBSE",
                    headers=headers,
                    json={
                        "inputs": {
                            "source_sentence": job_description,
                            "sentences": [resume_text]
                        }
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    sim_scores = response.json()
                    if isinstance(sim_scores, list) and len(sim_scores) > 0:
                        score = int(sim_scores[0] * 100)
            except Exception as e:
                logger.warning(f"AraBERT via Hugging Face Inference failed: {e}")

        if score is None:
            # Fallback to TF-IDF cosine similarity with Arabic stop words
            arabic_stop_words = {"من", "في", "على", "إلى", "هذا", "التي", "الذي", "هو", "هي", "تم", "عن", "مع", "كان", "كانت"}
            
            def get_tf_vector(text):
                words = [w for w in re.findall(r'[\u0600-\u06FF]+', text) if w not in arabic_stop_words]
                vector = defaultdict(int)
                for w in words:
                    vector[w] += 1
                return vector

            v1 = get_tf_vector(job_description)
            v2 = get_tf_vector(resume_text)

            intersection = set(v1.keys()) & set(v2.keys())
            numerator = sum([v1[x] * v2[x] for x in intersection])

            sum1 = sum([v1[x]**2 for x in v1.keys()])
            sum2 = sum([v2[x]**2 for x in v2.keys()])
            denominator = math.sqrt(sum1) * math.sqrt(sum2)

            if not denominator:
                score = 0
            else:
                score = int((float(numerator) / denominator) * 100)

        # Ensure score is bound between 0 and 100
        score = max(0, min(100, score))
        
        # Calculate matched and missing
        resume_words = set(re.findall(r'[\u0600-\u06FF]+', resume_text))
        matched = [w for w in unique_jd_kws if w in resume_words]
        missing = [w for w in unique_jd_kws if w not in resume_words]

        return {
            "match_percent": score,
            "total_jd_keywords": len(unique_jd_kws),
            "matched_keywords": matched,
            "missing_keywords": missing,
            "top_missing": [{"keyword": w, "importance": "high"} for w in missing[:20]],
            "top_matched": [{"keyword": w, "score": 10.0} for w in matched[:20]],
            "ats_tips": [
                "أضف الكلمات الدلالية المفقودة إلى سيرتك الذاتية لتحسين مطابقة نظام ATS.",
                "تأكد من صياغة خبراتك المهنية باستخدام الكلمات الرئيسية الواردة في وصف الوظيفة."
            ],
            "ats_breakdown": {
                "skills": score,
                "experience": score,
                "education": score
            },
            "missing_skills": missing[:10]
        }

    def calculate_match(
        self,
        resume_text: str,
        job_description: str,
    ) -> dict:
        # Check if the text contains Arabic characters
        if re.search(r"[\u0600-\u06ff]", resume_text + job_description):
            return self.calculate_arabic_match(resume_text, job_description)
        """
        Calculate match between resume and job description.

        Args:
            resume_text: The plain text content of the resume.
            job_description: The plain text content of the job description.

        Returns:
            A detailed breakdown dict with:
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
                "ats_tips": [
                    "⚠️ Job description appears empty. Paste the full JD for accurate scoring."
                ],
            }

        idf_weights = self._calculate_idf_weights(job_kw, job_description)
        matched, missing = self._match_keywords(resume_kw, job_kw, idf_weights)

        # Calculate mathematically sound weighted score
        total_earned_weight = 0.0
        total_possible_weight = 0.0

        for _kw, info in matched.items():
            max_kw_weight = info["weight"] * info["jd_frequency"]
            total_possible_weight += max_kw_weight
            total_earned_weight += info["weighted_score"] * info["jd_frequency"]

        for _kw, info in missing.items():
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

        # ── IMP-244: Keyword density analysis ──────────────────────────────
        # Density = matched keywords / total words in job description
        jd_word_count = max(len(job_description.split()), 1)
        keyword_density = round((len(matched) / jd_word_count) * 100, 2)

        # ── IMP-245: Job fit score explanation (why_matched / why_rejected) ─
        top_match_keywords = [kw for kw, _ in matched_sorted[:5]]
        top_miss_keywords = [kw for kw, _ in missing_sorted[:5]]

        why_matched: list[str] = []
        if top_match_keywords:
            why_matched.append(
                f"Your resume strongly matches on: {', '.join(top_match_keywords[:3])}."
            )
        if match_percent >= 70:
            why_matched.append("Overall keyword coverage exceeds ATS threshold of 70%.")
        elif match_percent >= 50:
            why_matched.append("Moderate keyword overlap — likely to pass basic ATS filters.")

        why_rejected: list[str] = []
        if top_miss_keywords:
            why_rejected.append(
                f"Critical missing keywords: {', '.join(top_miss_keywords[:3])}."
            )
        if match_percent < 50:
            why_rejected.append(
                "Match score below 50% — high risk of being filtered out by ATS before human review."
            )

        # ── IMP-246: Skill gap analysis (missing_skills list) ───────────────
        SKILL_INDICATORS = {"python", "java", "aws", "azure", "docker", "kubernetes",
                            "sql", "react", "node", "typescript", "golang", "rust",
                            "terraform", "ansible", "ci/cd", "cicd", "machine learning",
                            "deep learning", "nlp", "fastapi", "django", "flask"}
        missing_skills = [
            kw for kw, _ in missing_sorted
            if kw in SKILL_INDICATORS or kw in TECH_TAXONOMY
        ][:15]

        # ── IMP-248: Per-section ATS score breakdown ─────────────────────────
        def _section_score(section_keywords: set[str]) -> dict:
            """Score only keywords relevant to a CV section."""
            sec_matched = {k: v for k, v in matched.items() if k in section_keywords}
            sec_missing = {k: v for k, v in missing.items() if k in section_keywords}
            total = len(sec_matched) + len(sec_missing)
            pct = round((len(sec_matched) / max(total, 1)) * 100, 1)
            return {"score": pct, "matched": len(sec_matched), "missing": len(sec_missing)}

        SKILL_KW = TECH_TAXONOMY
        EXPERIENCE_KW = {"experience", "years", "senior", "junior", "lead", "manager",
                         "architect", "engineer", "developer", "analyst", "specialist",
                         "director", "vp", "head", "principal", "staff", "intern"}
        EDUCATION_KW = {"degree", "bachelor", "master", "phd", "mba", "university",
                        "college", "certification", "certified", "diploma", "graduate",
                        "ccna", "ccnp", "ccie", "aws certified", "azure", "gcp", "pmp",
                        "itil", "cissp", "cka", "ckad", "devnet"}

        ats_breakdown = {
            "skills":     _section_score(SKILL_KW),
            "experience": _section_score(EXPERIENCE_KW),
            "education":  _section_score(EDUCATION_KW),
        }

        return {
            "match_percent": match_percent,
            "total_jd_keywords": len(job_kw),
            "matched_keywords_count": len(matched),
            "missing_keywords_count": len(missing),
            "top_missing": [
                {
                    "keyword": kw,
                    "importance": round(info["weight"] * info["jd_frequency"], 2),
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
            # ── New enriched fields ──────────────────────────────────────────
            "keyword_density": keyword_density,          # IMP-244: density %
            "why_matched": why_matched,                  # IMP-245: strengths
            "why_rejected": why_rejected,                # IMP-245: weaknesses
            "missing_skills": missing_skills,            # IMP-246: skill gaps
            "ats_breakdown": ats_breakdown,              # IMP-248: section scores
        }

    # ── Tips Generator ─────────────────────────────────────────────────────

    def _generate_tips(
        self,
        match_percent: float,
        top_missing: list[tuple[str, dict]],
        total_jd: int,
        total_matched: int,
    ) -> list[str]:
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
                f"📌 Add these top keywords to your resume: {', '.join(keywords_5)}"
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

    def section_relevance(self, resume_sections: dict[str, str]) -> dict[str, float]:
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


_thread_pool = None

def _get_thread_pool():
    global _thread_pool
    if _thread_pool is None:
        import concurrent.futures
        _thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    return _thread_pool

def _run_async(coro):
    """Run an async coroutine from a synchronous context safely."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        executor = _get_thread_pool()
        future = executor.submit(asyncio.run, coro)
        return future.result()
    else:
        return asyncio.run(coro)


def analyze_with_groq(
    resume_text: str,
    jd_text: str,
    groq_key: str = DEFAULT_GROQ_KEY,
    model: str = "mixtral-8x7b-32768",
) -> dict:
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
) -> dict:
    """Async version of analyze_with_groq using LLMProviderPool with legacy Groq fallback."""
    import hashlib
    import json

    from core.edge_cache import edge_cache

    raw_key = f"{resume_text}:{jd_text}"
    cache_key = f"ats_match:{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()}"

    # Try retrieving from edge cache first
    try:
        if edge_cache.enabled:
            cached_val = await edge_cache.get(cache_key)
            if cached_val:
                logger.info("ATS Match cache hit! Returning in < 100ms.")
                if isinstance(cached_val, bytes):
                    cached_val = cached_val.decode('utf-8')
                return json.loads(cached_val)
    except Exception as cache_err:
        logger.warning(f"Failed to fetch ATS match from edge cache: {cache_err}")

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
                max_tokens=1000,
            )
            if content:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    res_dict = json.loads(json_match.group())
                    try:
                        if edge_cache.enabled:
                            await edge_cache.set(cache_key, json.dumps(res_dict), ex=86400)
                    except Exception as cache_err:
                        logger.warning(f"Failed to save ATS match to edge cache: {cache_err}")
                    return res_dict
        except Exception as pool_err:
            logger.warning(
                f"[ATS-Pool] Pool completion failed: {pool_err}. Falling back to direct Groq..."
            )

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
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    res_dict = json.loads(json_match.group())
                    try:
                        if edge_cache.enabled:
                            await edge_cache.set(cache_key, json.dumps(res_dict), ex=86400)
                    except Exception as cache_err:
                        logger.warning(f"Failed to save ATS match to edge cache: {cache_err}")
                    return res_dict
            else:
                logger.warning(
                    f"[ATS-Groq] API returned {resp.status_code}: {resp.text[:200]}"
                )
        except Exception as e:
            logger.error(f"[ATS-Groq] Async error: {e}")

    return {}


# ═══════════════════════════════════════════════════════════════════════════════
#  Combined Analysis (Algorithmic + Groq)
# ═══════════════════════════════════════════════════════════════════════════════


async def full_ats_analysis(
    resume_text: str,
    job_description: str,
    use_groq: bool = True,
    groq_key: str = DEFAULT_GROQ_KEY,
) -> dict:
    """
    Run both algorithmic (ATSMatcher) and Groq AI analysis, then merge results.

    Results are cached in Redis for 24 hours using a SHA256 cache key derived
    from the normalized resume + JD text. Falls back to uncached behavior if
    Redis is unavailable.

    This gives Sam the best of both worlds:
    - Fast, deterministic keyword matching (no API cost)
    - Deep semantic analysis from Groq (when enabled)
    - LLM call deduplication via Redis cache (zero cost for identical inputs)

    Args:
        resume_text: Full resume text
        job_description: Full job description
        use_groq: Whether to include Groq AI analysis
        groq_key: Groq API key

    Returns:
        Merged dict with both algorithmic + AI results
    """
    # Build deterministic cache key from normalized inputs
    def _norm(t):
        return re.sub(r"\s+", " ", t.strip().lower())
    cache_key = "ats:" + hashlib.sha256(
        (_norm(resume_text) + "||" + _norm(job_description)).encode("utf-8")
    ).hexdigest()

    # Try reading from Redis cache first
    from core.edge_cache import edge_cache
    cached_raw = None
    try:
        cached_raw = await edge_cache.get(cache_key)
        if cached_raw:
            logging.getLogger(__name__).debug(f"[ATSCache] Cache HIT for key {cache_key[:16]}...")
            cached_result = json.loads(cached_raw)
            cached_result["cache_hit"] = True
            return cached_result
    except Exception as e:
        logging.getLogger(__name__).warning(f"[ATSCache] Redis read failed, proceeding uncached: {e}")

    # Algorithmic match (always runs — zero cost)
    matcher = ATSMatcher()
    algo_result = matcher.calculate_match(resume_text, job_description)

    result = {
        "algorithmic": algo_result,
        "ai_analysis": {},
        "combined_score": algo_result["match_percent"],
        "source": "algorithmic",
        "cache_hit": False,
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
    ai_result_for_merge = result.get("ai_analysis", {})
    missing_set.update(ai_result_for_merge.get("missing_skills", []))
    result["all_missing_deduped"] = sorted(missing_set)

    # Store result in Redis cache (24h TTL)
    try:
        await edge_cache.set(cache_key, json.dumps(result), ex=86400)
        logging.getLogger(__name__).debug(f"[ATSCache] Stored result in cache key {cache_key[:16]}...")
    except Exception as e:
        logging.getLogger(__name__).warning(f"[ATSCache] Redis write failed: {e}")

    return result


# Alias for explicit usage with cache semantics
cached_full_ats_analysis = full_ats_analysis


# ═══════════════════════════════════════════════════════════════════════════════
#  Telegram Bot Command Hook
# ═══════════════════════════════════════════════════════════════════════════════


def format_ats_for_telegram(result: dict) -> str:
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


async def api_ats_score(
    resume_text: str,
    job_description: str,
    use_groq: bool = True,
    groq_key: str = DEFAULT_GROQ_KEY,
) -> dict:
    """
    API-friendly wrapper for full_ats_analysis.
    Designed to be called directly from FastAPI or Flask endpoints.

    Example FastAPI usage:
        @app.post("/api/ats-score")
        async def ats_score(payload: ATSRequest):
            return await api_ats_score(payload.resume, payload.jd)

    Returns serializable dict (no Python-specific objects).
    """
    return await full_ats_analysis(
        resume_text=resume_text,
        job_description=job_description,
        use_groq=use_groq,
        groq_key=groq_key,
    )


def parse_resume_from_file(filepath: str) -> str:
    """Read resume text from a file."""
    with open(filepath, encoding="utf-8", errors="replace") as f:
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
    logger.debug(f"Match Score: {result['match_percent']}%")
    logger.debug(f"Missing: {result['missing_keywords_count']} keywords")
    for kw_info in result["top_missing"][:5]:
        logger.debug(f"  ✗ {kw_info['keyword']} (imp: {kw_info['importance']})")

    logger.debug("\n── Telegram Preview ──")
    logger.debug(
        format_ats_for_telegram(
            {
                "algorithmic": result,
                "combined_score": result["match_percent"],
                "source": "algorithmic",
            }
        )
    )
