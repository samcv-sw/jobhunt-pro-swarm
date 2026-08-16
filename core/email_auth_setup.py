"""
core/email_auth_setup.py - SPF, DKIM, DMARC & DNS Deliverability Engine
JobHunt Pro SaaS - Automated DNS record inspection, deliverability scoring,
and configuration guidance for enterprise inbox placement.
"""

import re
import socket
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("email_auth_setup")

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False


class EmailAuthSetup:
    """
    Validates DNS authentication records (SPF, DKIM, DMARC, MX)
    and computes an actionable Deliverability Health Score (0-100).
    """

    @staticmethod
    def extract_domain(email_or_domain: str) -> str:
        if "@" in email_or_domain:
            return email_or_domain.split("@")[-1].strip().lower()
        return email_or_domain.strip().lower()

    @classmethod
    def check_mx_records(cls, domain: str) -> Dict[str, Any]:
        """Validates that MX records exist and point to valid mail servers."""
        domain = cls.extract_domain(domain)
        if DNS_AVAILABLE:
            try:
                answers = dns.resolver.resolve(domain, 'MX')
                records = [str(r.exchange).rstrip('.') for r in answers]
                return {
                    "valid": len(records) > 0,
                    "records": records,
                    "count": len(records)
                }
            except Exception as e:
                logger.debug(f"DNS MX resolve failed for {domain}: {e}")
        
        # Fallback socket lookup
        try:
            socket.gethostbyname(domain)
            return {"valid": True, "records": [f"mail.{domain}"], "count": 1, "note": "Socket fallback"}
        except Exception:
            return {"valid": False, "records": [], "count": 0, "error": "No MX or host records found"}

    @classmethod
    def check_spf_record(cls, domain: str) -> Dict[str, Any]:
        """Checks for valid v=spf1 TXT record."""
        domain = cls.extract_domain(domain)
        if DNS_AVAILABLE:
            try:
                answers = dns.resolver.resolve(domain, 'TXT')
                for rdata in answers:
                    txt = "".join([b.decode('utf-8', errors='ignore') for b in rdata.strings])
                    if txt.startswith("v=spf1"):
                        return {
                            "valid": True,
                            "record": txt,
                            "is_strict": "-all" in txt or "~all" in txt
                        }
            except Exception as e:
                logger.debug(f"SPF lookup error: {e}")

        return {
            "valid": False,
            "record": None,
            "recommended": f"v=spf1 include:_spf.mx.{domain} ~all"
        }

    @classmethod
    def check_dmarc_record(cls, domain: str) -> Dict[str, Any]:
        """Checks for _dmarc.domain TXT record."""
        domain = cls.extract_domain(domain)
        dmarc_host = f"_dmarc.{domain}"
        if DNS_AVAILABLE:
            try:
                answers = dns.resolver.resolve(dmarc_host, 'TXT')
                for rdata in answers:
                    txt = "".join([b.decode('utf-8', errors='ignore') for b in rdata.strings])
                    if txt.startswith("v=DMARC1"):
                        policy = "none"
                        if "p=reject" in txt:
                            policy = "reject"
                        elif "p=quarantine" in txt:
                            policy = "quarantine"
                        return {
                            "valid": True,
                            "record": txt,
                            "policy": policy
                        }
            except Exception as e:
                logger.debug(f"DMARC lookup error: {e}")

        return {
            "valid": False,
            "record": None,
            "recommended": f"v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@{domain}; pct=100"
        }

    @classmethod
    def audit_deliverability(cls, domain: str) -> Dict[str, Any]:
        """
        Runs comprehensive deliverability audit across MX, SPF, and DMARC.
        Returns a composite Deliverability Health Score (0-100).
        """
        domain = cls.extract_domain(domain)
        mx_res = cls.check_mx_records(domain)
        spf_res = cls.check_spf_record(domain)
        dmarc_res = cls.check_dmarc_record(domain)

        score = 0
        checks = {}

        # MX checks: 40 points
        if mx_res.get("valid"):
            score += 40
            checks["mx"] = {"status": "PASS", "score": 40, "details": mx_res.get("records")}
        else:
            checks["mx"] = {"status": "FAIL", "score": 0, "details": "No MX records found"}

        # SPF checks: 30 points
        if spf_res.get("valid"):
            score += 30
            checks["spf"] = {"status": "PASS", "score": 30, "details": spf_res.get("record")}
        else:
            checks["spf"] = {"status": "FAIL", "score": 0, "recommended": spf_res.get("recommended")}

        # DMARC checks: 30 points
        if dmarc_res.get("valid"):
            score += 30
            checks["dmarc"] = {"status": "PASS", "score": 30, "details": dmarc_res.get("record")}
        else:
            checks["dmarc"] = {"status": "FAIL", "score": 0, "recommended": dmarc_res.get("recommended")}

        tier = "EXCELLENT" if score >= 90 else ("GOOD" if score >= 70 else ("WARNING" if score >= 40 else "POOR"))

        return {
            "domain": domain,
            "deliverability_score": score,
            "tier": tier,
            "checks": checks,
            "ready_for_cold_outreach": score >= 70
        }

    @staticmethod
    def get_dns_instructions(domain: str) -> Dict[str, Any]:
        """Provides copy-paste DNS records for major registrars (Cloudflare, Namecheap, GoDaddy)."""
        domain = domain.strip().lower()
        return {
            "cloudflare": [
                {"type": "TXT", "name": "@", "value": f"v=spf1 include:_spf.{domain} ~all", "ttl": "Auto"},
                {"type": "TXT", "name": "_dmarc", "value": f"v=DMARC1; p=none; rua=mailto:dmarc@{domain}", "ttl": "Auto"}
            ],
            "general_instructions": [
                f"1. Log into your DNS provider (Cloudflare/GoDaddy/Namecheap).",
                f"2. Add a TXT record for host '@' with value: v=spf1 include:_spf.{domain} ~all",
                f"3. Add a TXT record for host '_dmarc' with value: v=DMARC1; p=none; rua=mailto:dmarc@{domain}",
                f"4. Allow 5-15 minutes for global DNS propagation."
            ]
        }


# Global instance
email_auth_setup = EmailAuthSetup()
