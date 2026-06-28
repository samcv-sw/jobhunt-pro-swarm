"""
JobHunt Pro v17.1 — Free Email Account Registrar
Auto-registers free email accounts from multiple providers for SMTP sending.
Zero investment — uses free signup flows via API/HTTP.
Providers: Mail.tm (instant), Temp-Mail, Guerrilla Mail, 10 Minute Mail,
           Yopmail, Outlook/Hotmail (limited), Gmail (requires phone).
"""
import re
import json
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

# ── Mail.tm API (FREE, instant, no phone needed) ────────────────
MAILTM_API = "https://api.mail.tm"
MAILTM_DOMAINS_URL = f"{MAILTM_API}/domains"
MAILTM_ACCOUNTS_URL = f"{MAILTM_API}/accounts"
MAILTM_TOKEN_URL = f"{MAILTM_API}/token"
MAILTM_MESSAGES_URL = f"{MAILTM_API}/messages"

# ── Guerrilla Mail API (FREE, instant, no phone) ─────────────────
GUERRILLA_MAIL_API = "https://api.guerrillamail.com/ajax.php"

# ── Temp-Mail API (FREE, instant) ────────────────────────────────
TEMPMAIL_API = "https://api.temp-mail.org"

# ── Common email domains for random generation ───────────────────
COMMON_DOMAINS = [
    "gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
    "protonmail.com", "mail.com", "yandex.com", "aol.com",
]

# ── Random username generators ───────────────────────────────────
ADJECTIVES = [
    "swift", "bright", "cool", "fast", "keen", "bold", "calm", "dark",
    "eager", "firm", "glad", "kind", "lite", "neat", "pure", "rare",
    "safe", "tall", "vast", "warm", "zest", "epic", "fair", "gold",
    "high", "jade", "keen", "lion", "mint", "nova", "onyx", "peak",
    "quik", "rich", "star", "true", "uber", "vibe", "wild", "zen",
]

NOUNS = [
    "wolf", "fox", "hawk", "owl", "bear", "deer", "dove", "fish",
    "frog", "hare", "kite", "lark", "lynx", "mole", "newt", "orca",
    "puma", "raya", "seal", "swan", "toad", "vole", "wren", "yeti",
    "arch", "beam", "clay", "dawn", "edge", "fern", "gale", "haze",
    "isle", "jazz", "knot", "lake", "mist", "nest", "oaks", "pine",
    "quiz", "reef", "sand", "tide", "vale", "wave", "yard", "zone",
]


def _random_username() -> str:
    """Generate a random username."""
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(10, 9999)
    return f"{adj}{noun}{num}"


def _random_password(length: int = 16) -> str:
    """Generate a random password."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
    return ''.join(random.choice(chars) for _ in range(length))


class FreeEmailRegistrar:
    """
    Auto-registers free email accounts from multiple providers.
    Each provider has different limits and verification requirements.
    """

    def __init__(self):
        self._client = httpx.Client(timeout=30.0)
        self._registered: List[Dict] = []
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        ]

    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': random.choice(self._user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
        }

    # ── Mail.tm (BEST: instant, no phone, unlimited) ─────────────
    def register_mailtm(self) -> Optional[Dict]:
        """
        Register a free Mail.tm account.
        Returns: {email, password, token} or None on failure.
        Mail.tm is the best option — instant, no phone verification, unlimited accounts.
        """
        try:
            # Get available domains
            resp = self._client.get(MAILTM_DOMAINS_URL, headers=self._get_headers())
            if resp.status_code != 200:
                logger.debug("Mail.tm: failed to fetch domains")
                return None

            domains = resp.json().get('hydra:member', [])
            if not domains:
                logger.debug("Mail.tm: no domains available")
                return None

            domain = domains[0]['domain']
            username = _random_username()
            password = _random_password()
            email = f"{username}@{domain}"

            # Create account
            resp = self._client.post(
                MAILTM_ACCOUNTS_URL,
                headers=self._get_headers(),
                json={
                    'address': email,
                    'password': password,
                },
            )

            if resp.status_code not in (200, 201):
                logger.debug(f"Mail.tm: registration failed: {resp.status_code}")
                return None

            # Get auth token
            resp = self._client.post(
                MAILTM_TOKEN_URL,
                headers=self._get_headers(),
                json={'address': email, 'password': password},
            )

            if resp.status_code != 200:
                logger.debug("Mail.tm: token fetch failed")
                return None

            token = resp.json().get('token', '')

            account = {
                'provider': 'mailtm',
                'email': email,
                'password': password,
                'token': token,
                'smtp_host': None,  # Mail.tm is web-only, no SMTP
                'smtp_port': None,
                'daily_limit': 100,  # Conservative estimate
            }
            self._registered.append(account)
            logger.info(f"Mail.tm: registered {email}")
            return account

        except Exception as e:
            logger.debug(f"Mail.tm: error: {e}")
            return None

    # ── Guerrilla Mail (FREE, instant, disposable) ──────────────
    def register_guerrillamail(self) -> Optional[Dict]:
        """
        Register a free Guerrilla Mail account.
        Returns: {email, email_hash, alias} or None.
        Good for receiving verification emails.
        """
        try:
            resp = self._client.post(
                GUERRILLA_MAIL_API,
                params={
                    'f': 'get_email_address',
                    'ip': '',
                    'agent': 'JobHunt Pro',
                },
                headers=self._get_headers(),
            )

            if resp.status_code != 200:
                return None

            data = resp.json()
            email = data.get('email_addr', '')
            email_hash = data.get('email_hash', '')
            alias = data.get('alias', '')

            if not email:
                return None

            account = {
                'provider': 'guerrillamail',
                'email': email,
                'password': '',
                'token': email_hash,
                'email_hash': email_hash,
                'alias': alias,
                'smtp_host': None,
                'smtp_port': None,
                'daily_limit': 50,
            }
            self._registered.append(account)
            logger.info(f"Guerrilla Mail: registered {email}")
            return account

        except Exception as e:
            logger.debug(f"Guerrilla Mail: error: {e}")
            return None

    # ── Register batch of accounts ──────────────────────────────
    def register_batch(self, count: int = 5, providers: List[str] = None) -> List[Dict]:
        """
        Register multiple free email accounts.
        Args:
            count: Number of accounts to register
            providers: List of providers to use (default: all)
        Returns: List of account dicts
        """
        if providers is None:
            providers = ['mailtm', 'guerrillamail']

        accounts = []
        provider_cycle = providers * (count // len(providers) + 1)

        for i in range(count):
            provider = provider_cycle[i % len(provider_cycle)]
            account = None

            if provider == 'mailtm':
                account = self.register_mailtm()
            elif provider == 'guerrillamail':
                account = self.register_guerrillamail()

            if account:
                accounts.append(account)
                logger.info(f"Registered {account['email']} via {provider}")
            else:
                logger.warning(f"Failed to register via {provider}")

            # Rate limit between registrations
            time.sleep(random.uniform(2.0, 5.0))

        return accounts

    def get_registered_accounts(self) -> List[Dict]:
        """Get all registered accounts."""
        return self._registered

    def get_stats(self) -> Dict:
        return {
            'total_registered': len(self._registered),
            'by_provider': {},
        }

    def close(self):
        try:
            self._client.close()
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────
_registrar: Optional[FreeEmailRegistrar] = None


def get_registrar() -> FreeEmailRegistrar:
    global _registrar
    if _registrar is None:
        _registrar = FreeEmailRegistrar()
    return _registrar


def register_free_emails(count: int = 5) -> List[Dict]:
    """Convenience function to register free email accounts."""
    registrar = get_registrar()
    return registrar.register_batch(count=count)


# ── Quick test ───────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    accounts = register_free_emails(count=3)
    print(f"Registered {len(accounts)} accounts:")
    for acc in accounts:
        print(f"  - {acc['email']} ({acc['provider']})")
