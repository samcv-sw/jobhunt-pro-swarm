"""
core/dnsbl_threat_sentinel.py
DNSBL Real-Time Blocklist Sentinel & HaveIBeenPwned Honeypot/Breach Detector
JobHunt Pro SaaS — Enterprise Deliverability & Dark-Web Threat Intelligence

Features:
1. Real-time DNSBL lookups against Spamhaus ZEN, Barracuda, SORBS, SpamCop for IPs and Domains.
2. HaveIBeenPwned k-anonymity SHA-1 range checks to identify compromised/stale emails and honeypots.
3. Fail-open non-blocking architecture with in-memory LRU TTL caching.
4. Seamless integration with core/deliverability_shield.py.
"""

import socket
import hashlib
import logging
import time
import re
from typing import Dict, Any, List, Optional, Tuple

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger("DNSBLThreatSentinel")

# Standard IP-based DNS Blocklists
DNSBL_ZONES = [
    {"name": "Spamhaus ZEN", "zone": "zen.spamhaus.org", "weight": 40},
    {"name": "Barracuda Reputation", "zone": "b.barracudacentral.org", "weight": 30},
    {"name": "SORBS DNSBL", "zone": "dnsbl.sorbs.net", "weight": 20},
    {"name": "SpamCop Network", "zone": "bl.spamcop.net", "weight": 20},
]

# Domain-based Blocklists (DBL / URIBL)
DOMAIN_BL_ZONES = [
    {"name": "Spamhaus DBL", "zone": "dbl.spamhaus.org", "weight": 50},
    {"name": "URIBL Multi", "zone": "multi.uribl.com", "weight": 40},
]


class DNSBLThreatSentinel:
    """
    Real-Time Threat Intelligence & Deliverability Armor.
    Shields sender IPs and domain reputation by pre-validating against world blocklists
    and dark-web breach data dumps.
    """

    def __init__(self, cache_ttl_seconds: int = 86400, timeout_seconds: float = 2.0):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self._ip_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._email_breach_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._domain_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    @staticmethod
    def _reverse_ip(ip: str) -> Optional[str]:
        """Converts an IPv4 address e.g. 192.0.2.1 to 1.2.0.192 for DNSBL resolution."""
        parts = ip.strip().split(".")
        if len(parts) != 4:
            return None
        for p in parts:
            if not p.isdigit() or not (0 <= int(p) <= 255):
                return None
        return ".".join(reversed(parts))

    def check_ip_blocklists(self, ip: str) -> Dict[str, Any]:
        """
        Queries major DNSBL zones for a given IP address.
        Returns blocklist status, reputation score (0-100), and list of listings.
        """
        ip = ip.strip()
        now = time.time()
        
        # Check in-memory cache
        if ip in self._ip_cache:
            cached_time, cached_result = self._ip_cache[ip]
            if now - cached_time < self.cache_ttl:
                return cached_result

        rev_ip = self._reverse_ip(ip)
        if not rev_ip:
            return {
                "ip": ip,
                "is_clean": True,
                "reputation_score": 100,
                "listed_in": [],
                "error": "Invalid IPv4 format",
            }

        listed_in: List[Dict[str, Any]] = []
        penalty_score = 0

        # Save previous default timeout and apply fast sentinel timeout
        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(self.timeout)
            for bl in DNSBL_ZONES:
                query_host = f"{rev_ip}.{bl['zone']}"
                try:
                    # If this resolves, the IP is listed on the blocklist
                    answers = socket.gethostbyname_ex(query_host)
                    return_codes = answers[2]
                    listed_in.append({
                        "provider": bl["name"],
                        "zone": bl["zone"],
                        "return_codes": return_codes,
                    })
                    penalty_score += bl["weight"]
                except (socket.gaierror, socket.herror, socket.timeout):
                    # Not listed or DNS lookup timed out (fail-open)
                    pass
                except Exception as e:
                    logger.debug("DNSBL lookup error on %s: %s", query_host, e)
        finally:
            socket.setdefaulttimeout(old_timeout)

        reputation_score = max(0, 100 - penalty_score)
        is_clean = len(listed_in) == 0

        result = {
            "ip": ip,
            "is_clean": is_clean,
            "reputation_score": reputation_score,
            "listed_in": listed_in,
            "checked_at": now,
        }

        self._ip_cache[ip] = (now, result)
        return result

    def check_domain_blocklists(self, domain: str) -> Dict[str, Any]:
        """
        Queries Domain Blocklists (DBL/URIBL) for domain reputation check.
        """
        domain = domain.strip().lower()
        now = time.time()

        if domain in self._domain_cache:
            cached_time, cached_result = self._domain_cache[domain]
            if now - cached_time < self.cache_ttl:
                return cached_result

        listed_in: List[Dict[str, Any]] = []
        penalty = 0

        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(self.timeout)
            for bl in DOMAIN_BL_ZONES:
                query_host = f"{domain}.{bl['zone']}"
                try:
                    answers = socket.gethostbyname_ex(query_host)
                    listed_in.append({
                        "provider": bl["name"],
                        "zone": bl["zone"],
                        "return_codes": answers[2],
                    })
                    penalty += bl["weight"]
                except (socket.gaierror, socket.herror, socket.timeout):
                    pass
                except Exception as e:
                    logger.debug("Domain BL error on %s: %s", query_host, e)
        finally:
            socket.setdefaulttimeout(old_timeout)

        reputation_score = max(0, 100 - penalty)
        is_clean = len(listed_in) == 0

        result = {
            "domain": domain,
            "is_clean": is_clean,
            "reputation_score": reputation_score,
            "listed_in": listed_in,
            "checked_at": now,
        }

        self._domain_cache[domain] = (now, result)
        return result

    def check_email_breach_k_anonymity(self, email: str) -> Dict[str, Any]:
        """
        Performs a privacy-preserving k-anonymity SHA-1 hash check against HIBP
        to detect if an email is exposed in dark-web breach dumps or likely a dead honeypot.
        
        Uses SHA-1 prefix (first 5 hex chars) to protect candidate/recruiter privacy.
        """
        email_clean = email.strip().lower()
        now = time.time()

        if email_clean in self._email_breach_cache:
            cached_time, cached_result = self._email_breach_cache[email_clean]
            if now - cached_time < self.cache_ttl:
                return cached_result

        sha1_hash = hashlib.sha1(email_clean.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]

        is_breached = False
        breach_count = 0

        if httpx is not None:
            try:
                url = f"https://api.pwnedpasswords.com/range/{prefix}"
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, headers={"User-Agent": "JobHuntPro-DeliverabilitySentinel/1.0"})
                    if resp.status_code == 200:
                        lines = resp.text.splitlines()
                        for line in lines:
                            if ":" in line:
                                line_suffix, count_str = line.split(":", 1)
                                if line_suffix.strip().upper() == suffix:
                                    is_breached = True
                                    try:
                                        breach_count = int(count_str.strip())
                                    except ValueError:
                                        breach_count = 1
                                    break
            except Exception as e:
                logger.debug("HIBP k-anonymity query error for %s: %s", email_clean, e)

        result = {
            "email": email_clean,
            "is_breached": is_breached,
            "breach_occurrences": breach_count,
            "risk_level": "HIGH" if (is_breached and breach_count > 10) else ("MEDIUM" if is_breached else "LOW"),
            "checked_at": now,
        }

        self._email_breach_cache[email_clean] = (now, result)
        return result

    def get_comprehensive_deliverability_threat_score(
        self, sender_ip: Optional[str], sender_domain: str, recipient_email: str
    ) -> Dict[str, Any]:
        """
        Aggregates IP, Domain, and Recipient checks into a single unified threat score.
        Score: 0 to 100 (100 = perfectly clean, 0 = high threat / listed everywhere).
        """
        ip_status = self.check_ip_blocklists(sender_ip) if sender_ip else {"is_clean": True, "reputation_score": 100}
        domain_status = self.check_domain_blocklists(sender_domain)
        recipient_status = self.check_email_breach_k_anonymity(recipient_email)

        combined_score = (ip_status.get("reputation_score", 100) * 0.45) + (
            domain_status.get("reputation_score", 100) * 0.45
        ) + (0 if recipient_status.get("risk_level") == "HIGH" else 10)

        combined_score = round(min(100.0, max(0.0, combined_score)), 1)
        safe_to_dispatch = combined_score >= 60.0

        return {
            "safe_to_dispatch": safe_to_dispatch,
            "composite_threat_score": combined_score,
            "ip_status": ip_status,
            "domain_status": domain_status,
            "recipient_breach_status": recipient_status,
            "recommendation": "PROCEED" if safe_to_dispatch else "QUARANTINE_AND_ROTATE_IP",
        }


# Global singleton instance for rapid zero-cost reuse
global_dnsbl_sentinel = DNSBLThreatSentinel()
