"""
ANTI-BAN PROTECTION SYSTEM
Ported from Rita Project - Makes bot look human to avoid detection
"""

import random
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)


class AntiBanProtection:
    """
    Protects email sending from being detected and banned.
    
    Features:
    - Human-like timing patterns
    - Rate limiting per company
    - Honeypot detection
    - Suspicious company detection
    - Application spacing
    """
    
    def __init__(self):
        # Track applications per company
        self.company_applications: Dict[str, List[datetime]] = {}
        
        # Blacklist of suspicious/honeypot companies
        self.suspicious_companies: Set[str] = set()
        
        # Track failed applications
        self.failed_applications: Dict[str, int] = {}
        
        # Honeypot indicators
        self.honeypot_keywords = {
            'honeypot', 'trap', 'automated',
            'spam', 'scam', 'phishing',
            'crawler', 'scraper'
        }
        
        # Suspicious patterns
        self.suspicious_patterns = {
            'too_good': ['$500k', '$1M', 'million dollar', 'instant hire', 'no experience needed'],
            'vague': ['various positions', 'multiple roles', 'any position', 'flexible role'],
            'urgent': ['urgent', 'immediate', 'asap', 'right now', 'today only'],
            'suspicious_email': ['noreply', 'no-reply', 'donotreply', 'test@', 'admin@']
        }
        
        # Rate limits
        self.max_apps_per_company_per_day = 1
        self.max_apps_per_company_per_week = 2
        self.max_apps_per_company_total = 5
        self.min_time_between_apps = 2  # 2 seconds minimum
        self.max_apps_per_hour = 50  # Conservative
        self.max_apps_per_day = 200  # Conservative
        
        # Timing
        self.last_application_time = None
        self.daily_applications = 0
        self.daily_reset_time = datetime.now()
        self.hourly_applications = 0
        self.hourly_reset_time = datetime.now()
    
    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for tracking"""
        return company_name.lower().strip().replace(' ', '_')
    
    def is_honeypot(self, email: str, company: str, snippet: str = "") -> bool:
        """Check if this looks like a honeypot/spam trap"""
        email_lower = email.lower()
        company_lower = company.lower()
        snippet_lower = snippet.lower()
        
        # Check email for honeypot keywords
        for keyword in self.honeypot_keywords:
            if keyword in email_lower:
                logger.warning(f"HONEYPOT detected: {email} contains '{keyword}'")
                return True
        
        # Check for suspicious email patterns
        suspicious_email_patterns = ['noreply', 'no-reply', 'donotreply', 'test@', 'admin@']
        for pattern in suspicious_email_patterns:
            if pattern in email_lower:
                logger.warning(f"Suspicious email pattern: {email} contains '{pattern}'")
                return True
        
        # Check company for suspicious patterns
        for category, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in snippet_lower:
                    logger.warning(f"Suspicious pattern ({category}): {company} - '{pattern}'")
                    return True
        
        return False
    
    def can_apply_to_company(self, company: str) -> tuple[bool, str]:
        """Check if we can apply to this company"""
        company_key = self._normalize_company_name(company)
        now = datetime.now()
        
        # Check if company is blacklisted
        if company_key in self.suspicious_companies:
            return False, "Company is blacklisted"
        
        # Get application history
        apps = self.company_applications.get(company_key, [])
        
        # Clean old entries
        apps = [app for app in apps if (now - app).days < 30]
        self.company_applications[company_key] = apps
        
        # Check daily limit
        daily_apps = [app for app in apps if (now - app).days < 1]
        if len(daily_apps) >= self.max_apps_per_company_per_day:
            return False, f"Daily limit reached ({self.max_apps_per_company_per_day}/day)"
        
        # Check weekly limit
        weekly_apps = [app for app in apps if (now - app).days < 7]
        if len(weekly_apps) >= self.max_apps_per_company_per_week:
            return False, f"Weekly limit reached ({self.max_apps_per_company_per_week}/week)"
        
        # Check total limit
        if len(apps) >= self.max_apps_per_company_total:
            return False, f"Total limit reached ({self.max_apps_per_company_total} total)"
        
        return True, "OK"
    
    def record_application(self, company: str):
        """Record an application to a company"""
        company_key = self._normalize_company_name(company)
        now = datetime.now()
        
        if company_key not in self.company_applications:
            self.company_applications[company_key] = []
        
        self.company_applications[company_key].append(now)
        self.last_application_time = now
        self.daily_applications += 1
        self.hourly_applications += 1
        
        logger.debug(f"Recorded application to {company}")
    
    def record_failure(self, company: str):
        """Record a failed application"""
        company_key = self._normalize_company_name(company)
        
        if company_key not in self.failed_applications:
            self.failed_applications[company_key] = 0
        
        self.failed_applications[company_key] += 1
        
        # Blacklist after 3 failures
        if self.failed_applications[company_key] >= 3:
            self.suspicious_companies.add(company_key)
            logger.warning(f"Blacklisted {company} after {self.failed_applications[company_key]} failures")
    
    def should_blacklist_company(self, company: str) -> bool:
        """Check if company should be blacklisted"""
        company_key = self._normalize_company_name(company)
        
        # Check failure count
        failures = self.failed_applications.get(company_key, 0)
        if failures >= 3:
            return True
        
        # Check if already blacklisted
        if company_key in self.suspicious_companies:
            return True
        
        return False
    
    def get_delay_before_next(self) -> float:
        """Get delay before next application (human-like)"""
        now = datetime.now()
        
        # Reset hourly counter
        if (now - self.hourly_reset_time).seconds >= 3600:
            self.hourly_applications = 0
            self.hourly_reset_time = now
        
        # Reset daily counter
        if (now - self.daily_reset_time).days >= 1:
            self.daily_applications = 0
            self.daily_reset_time = now
        
        # Check hourly limit
        if self.hourly_applications >= self.max_apps_per_hour:
            # Wait until next hour
            wait_time = 3600 - (now - self.hourly_reset_time).seconds
            logger.warning(f"Hourly limit reached. Waiting {wait_time}s")
            return wait_time
        
        # Check daily limit
        if self.daily_applications >= self.max_apps_per_day:
            # Wait until tomorrow
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            wait_time = (tomorrow - now).seconds
            logger.warning(f"Daily limit reached. Waiting {wait_time}s")
            return wait_time
        
        # Base delay with jitter
        base_delay = self.min_time_between_apps
        jitter = random.uniform(0.5, 2.0)  # 0.5-2s jitter
        delay = base_delay + jitter
        
        # Add extra delay if last application was too recent
        if self.last_application_time:
            time_since_last = (now - self.last_application_time).seconds
            if time_since_last < self.min_time_between_apps:
                extra_delay = self.min_time_between_apps - time_since_last
                delay += extra_delay
        
        return delay
    
    async def wait_for_safe_timing(self):
        """Wait for safe timing between applications"""
        delay = self.get_delay_before_next()
        if delay > 0:
            logger.debug(f"Waiting {delay:.1f}s before next application")
            await asyncio.sleep(delay)
    
    def get_stats(self) -> Dict:
        """Get anti-ban statistics"""
        return {
            "daily_applications": self.daily_applications,
            "hourly_applications": self.hourly_applications,
            "blacklisted_companies": len(self.suspicious_companies),
            "tracked_companies": len(self.company_applications),
            "total_failures": sum(self.failed_applications.values())
        }


# Global instance
anti_ban = AntiBanProtection()
