"""
JobHunt Pro v13 — Multi-Provider Email Rotator Pool
Rotates across Gmail, Brevo, SendGrid, Zoho, Outlook to maximize free-tier sending.
500+ emails/day with zero cost by rotating across providers.
"""
import asyncio
import logging
import smtplib
import ssl
import time
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date

import config

logger = logging.getLogger(__name__)

# Database rate-limiting synchronization cache
_db_rate_limited_hosts = {}
_last_db_rate_limit_check = 0.0

def _load_db_rate_limits():
    """Load rate-limited SMTP hosts from the database to synchronize state across instances."""
    global _db_rate_limited_hosts, _last_db_rate_limit_check
    now = time.time()
    if now - _last_db_rate_limit_check < 60.0:  # Cache for 60 seconds
        return
        
    _last_db_rate_limit_check = now
    new_limits = {}
    conn = None
    try:
        # Try importing from the FastAPI app instance first
        from web.app_v2 import get_db
        conn = get_db()
    except Exception:
        try:
            # Fallback to direct sqlite3 connector (which uses pg_sqlite_shim under CLOUD_MODE)
            import sqlite3
            import config
            from pathlib import Path
            db_name = getattr(config, "DB_PATH", None) or os.getenv("DB_PATH") or "jobhunt_saas_v2.db"
            db_path = str(Path(__file__).parent.parent / db_name)
            conn = sqlite3.connect(db_path, timeout=10)
            conn.row_factory = sqlite3.Row
        except Exception:
            pass

    if conn:
        try:
            # Check for SMTP accounts flagged as rate limited within the last 1 hour
            rows = conn.execute(
                "SELECT smtp_host FROM smtp_rotation WHERE rate_limited = 1 AND limited_at > datetime('now', '-1 hour')"
            ).fetchall()
            for r in rows:
                if isinstance(r, dict):
                    host = r.get("smtp_host")
                elif hasattr(r, "keys") and "smtp_host" in r.keys():
                    host = r["smtp_host"]
                else:
                    host = r[0]
                if host:
                    new_limits[host] = True
        except Exception as e:
            logger.debug(f"[RotatorPool] Failed to query smtp_rotation: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
                
    _db_rate_limited_hosts = new_limits


@dataclass
class EmailAccount:
    name: str
    server: str
    port: int
    user: str
    password: str
    daily_limit: int
    weight: int = 1
    use_tls: bool = True

    @property
    def is_configured(self) -> bool:
        return bool(self.user) and bool(self.password)

    @property
    def provider_type(self) -> str:
        """Categorize the provider type."""
        if "gmail" in self.server:
            return "gmail"
        if "sendgrid" in self.server:
            return "sendgrid"
        if "zoho" in self.server:
            return "zoho"
        if "outlook" in self.server or "office365" in self.server or "live" in self.server:
            return "outlook"
        if "mailgun" in self.server:
            return "mailgun"
        if "yahoo" in self.server:
            return "yahoo"
        if "mailjet" in self.server:
            return "mailjet"
        return "other"


class SMTPConnectionPool:
    """
    High-performance SMTP Connection Pooling (Skeleton).
    In a Maximum Power architecture, this manages 10-50 simultaneous TLS connections 
    per provider to avoid handshake overhead on every batch send.
    """
    def __init__(self, account: EmailAccount, max_connections: int = 10):
        self.account = account
        self.max_connections = max_connections
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self._active_connections = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> smtplib.SMTP:
        """Acquire a warm SMTP connection from the pool."""
        # Implementation left for production rollout
        pass

    async def release(self, conn: smtplib.SMTP):
        """Return the connection to the pool."""
        pass



class EmailSenderClient:
    """Manages SMTP connection for a single email account with quota tracking."""

    def __init__(self, account: EmailAccount):
        self.account = account
        self._sent_today = 0
        self._daily_reset = date.today()
        self._consecutive_failures = 0
        self._last_error: Optional[str] = None
        self._available = True
        self._lock = asyncio.Lock()
        self._smtp_conn: Optional[smtplib.SMTP] = None
        self._conn_lock = asyncio.Lock()

    def _reset_daily_if_needed(self):
        today = date.today()
        if today != self._daily_reset:
            self._sent_today = 0
            self._daily_reset = today
            self._available = True

    def can_send(self) -> bool:
        """Check if this account can send more emails today."""
        self._reset_daily_if_needed()
        if not self._available:
            return False
            
        # Check database rate-limiting state
        try:
            _load_db_rate_limits()
            if self.account.server in _db_rate_limited_hosts:
                logger.warning(f"SMTP account {self.account.name} ({self.account.server}) bypassed: marked rate-limited in DB.")
                return False
        except Exception as e:
            logger.debug(f"Failed to check db rate limits: {e}")
            
        return self._sent_today < self.account.daily_limit

    def quota_remaining(self) -> int:
        self._reset_daily_if_needed()
        return max(0, self.account.daily_limit - self._sent_today)

    async def _connect(self) -> bool:
        """Establish SMTP connection."""
        try:
            loop = asyncio.get_event_loop()

            def _connect_sync():
                if self.account.use_tls:
                    ctx = ssl.create_default_context()
                    smtp = smtplib.SMTP(self.account.server, self.account.port, timeout=30)
                    smtp.ehlo()
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                else:
                    smtp = smtplib.SMTP_SSL(
                        self.account.server, self.account.port, timeout=30
                    )
                    smtp.ehlo()
                smtp.login(self.account.user, self.account.password)
                return smtp

            self._smtp_conn = await loop.run_in_executor(None, _connect_sync)
            logger.debug(
                f"SMTP connected: {self.account.name} ({self.account.user})"
            )
            return True
        except smtplib.SMTPAuthenticationError:
            self._last_error = "SMTP authentication failed"
            self._available = False
            logger.error(
                f"SMTP auth failed for {self.account.name} ({self.account.user})"
            )
            return False
        except Exception as e:
            self._last_error = str(e)
            logger.warning(f"SMTP connect failed for {self.account.name}: {e}")
            return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Send an email through this account. Returns True on success."""
        async with self._lock:
            self._reset_daily_if_needed()
            if not self.can_send():
                return False

            if self._smtp_conn is None:
                connected = await self._connect()
                if not connected:
                    return False
            else:
                # Verify connection is still alive
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._smtp_conn.noop)
                except Exception:
                    logger.debug(f"SMTP connection stale for {self.account.name}, reconnecting")
                    try:
                        self._smtp_conn.quit()
                    except Exception:
                        pass
                    self._smtp_conn = None
                    connected = await self._connect()
                    if not connected:
                        return False

            msg = MIMEMultipart("mixed")
            msg["From"] = self.account.user
            msg["To"] = to_email
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to

            alt_part = MIMEMultipart("alternative")
            if body_text:
                alt_part.attach(MIMEText(body_text, "plain", "utf-8"))
            alt_part.attach(MIMEText(body_html, "html", "utf-8"))
            msg.attach(alt_part)

            if attachments:
                for path in attachments:
                    if path and os.path.exists(path):
                        with open(path, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(path)
                            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                            msg.attach(part)

            try:
                loop = asyncio.get_event_loop()

                def _send_sync():
                    return self._smtp_conn.sendmail(
                        self.account.user, to_email, msg.as_string()
                    )

                refused = await loop.run_in_executor(None, _send_sync)
                if refused:
                    logger.warning(f"[Rotator] Refused via {self.account.name}: {refused}")
                    return False
                self._sent_today += 1
                self._consecutive_failures = 0
                logger.debug(
                    f"Email sent via {self.account.name} -> {to_email} "
                    f"({self._sent_today}/{self.account.daily_limit} today)"
                )
                return True

            except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused,
                    smtplib.SMTPRecipientsRefused, smtplib.SMTPDataError) as e:
                self._consecutive_failures += 1
                self._last_error = str(e)
                self._smtp_conn = None  # Force reconnect next time
                logger.warning(f"SMTP error on {self.account.name}: {e}")
                if self._consecutive_failures > 5:
                    self._available = False
                return False

            except Exception as e:
                self._consecutive_failures += 1
                self._last_error = str(e)
                self._smtp_conn = None
                logger.warning(f"Email send error on {self.account.name}: {e}")
                return False

    async def disconnect(self):
        if self._smtp_conn:
            try:
                loop = asyncio.get_event_loop()

                def _quit():
                    try:
                        self._smtp_conn.quit()
                    except Exception:
                        pass

                await loop.run_in_executor(None, _quit)
            except Exception:
                pass
            self._smtp_conn = None


class EmailRotatorPool:
    """
    Manages multiple email accounts, rotating across them to maximize daily sending.
    Automatically skips accounts that are out of quota or having errors.
    """

    def __init__(self):
        self._accounts: List[EmailSenderClient] = []
        self._round_robin_idx = 0
        self._lock = asyncio.Lock()
        self._stats_file = "cache/email_rotator_stats.json"

    def get_provider(self, preferred_account: Optional[str] = None) -> Optional[EmailSenderClient]:
        """
        Get the next available email provider (round-robin, respecting daily quotas).
        Returns None if all accounts are exhausted.
        """
        if not self._accounts:
            return None

        # If a preferred account is specified and available, return it
        if preferred_account:
            for acc in self._accounts:
                if acc.account.name == preferred_account and acc.can_send():
                    return acc

        # Round-robin across available accounts
        accounts = self.get_available_accounts()
        if not accounts:
            return None

        for _ in range(len(accounts)):
            idx = self._round_robin_idx % len(accounts)
            self._round_robin_idx += 1
            acc = accounts[idx]
            if acc.can_send():
                return acc

        return None

    def release_provider(self, account: EmailSenderClient):
        """
        Release a provider back to the pool.
        No-op in current design — providers are stateless between sends;
        kept for API compatibility with pool-based architectures.
        """
        logger.debug(f"Provider {account.account.name} released back to pool")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive pool statistics.
        Alias for get_pool_status().
        """
        return await self.get_pool_status()

    def load_config(self) -> "EmailRotatorPool":
        """Load accounts from config.py EMAIL_PROVIDERS list."""
        configured = 0
        for provider in config.EMAIL_PROVIDERS:
            account = EmailAccount(
                name=provider["name"],
                server=provider["server"],
                port=provider["port"],
                user=provider["user"],
                password=provider["password"],
                daily_limit=provider.get("daily_limit", 100),
                weight=provider.get("weight", 1),
            )
            if account.is_configured:
                self._accounts.append(EmailSenderClient(account))
                configured += 1
                logger.info(
                    f"Email account loaded: {account.name} ({account.user}) "
                    f"limit={account.daily_limit}/day"
                )

        logger.info(
            f"EmailRotatorPool: {configured} accounts loaded, "
            f"total daily capacity: {self.get_total_daily_capacity()}"
        )
        self._load_persisted_stats()
        return self

    def get_total_daily_capacity(self) -> int:
        return sum(a.account.daily_limit for a in self._accounts)

    def get_available_accounts(self) -> List[EmailSenderClient]:
        return [a for a in self._accounts if a.can_send()]

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        preferred_account: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Send email by finding best available account.
        Returns (success, account_name_or_error).
        """
        if tenant_id:
            try:
                from core.multi_tenant import MultiTenantRunner
                provider = MultiTenantRunner.get_tenant_smtp_provider(tenant_id)
                if provider and provider.get("user") and provider.get("password"):
                    from core.email_rotator_pool import EmailAccount, EmailSenderClient
                    account = EmailAccount(
                        name=provider.get("name", f"tenant_{tenant_id}"),
                        server=provider["server"],
                        port=provider["port"],
                        user=provider["user"],
                        password=provider["password"],
                        daily_limit=provider.get("daily_limit", 100),
                        weight=provider.get("weight", 1)
                    )
                    tenant_client = EmailSenderClient(account)
                    success = await tenant_client.send_email(
                        to_email, subject, body_html, body_text, attachments=attachments
                    )
                    return success, account.name if success else tenant_client._last_error
            except Exception as e:
                logger.error(f"[EmailRotatorPool] Failed to send via tenant SMTP provider: {e}")

        async with self._lock:
            if not self._accounts:
                logger.error("No email accounts configured")
                return False, "No email accounts configured"

            accounts = self.get_available_accounts()
            if not accounts:
                logger.warning("All email accounts exhausted for today")
                return False, "All accounts out of quota"

            # If preferred account is specified and available, use it
            if preferred_account:
                for acc in accounts:
                    if acc.account.name == preferred_account:
                        success = await acc.send_email(
                            to_email, subject, body_html, body_text, attachments=attachments
                        )
                        self._persist_stats()
                        return success, acc.account.name if success else acc._last_error

            # Round-robin across available accounts
            for _ in range(len(accounts)):
                idx = self._round_robin_idx % len(accounts)
                self._round_robin_idx += 1
                acc = accounts[idx]
                success = await acc.send_email(
                    to_email, subject, body_html, body_text, attachments=attachments
                )
                if success:
                    self._persist_stats()
                    return True, acc.account.name

            self._persist_stats()
            return False, "All accounts failed to send"

    async def send_batch(
        self,
        emails: List[Tuple[str, str, str, Optional[str]]],
    ) -> Dict[str, Any]:
        """
        Send multiple emails, distributing across available accounts.
        Each tuple: (to_email, subject, body_html, body_text_or_None)
        """
        results = {
            "total": len(emails),
            "sent": 0,
            "failed": 0,
            "by_account": {},
            "failures": [],
        }

        for to_email, subject, body_html, body_text in emails:
            success, info = await self.send_email(to_email, subject, body_html, body_text)
            if success:
                results["sent"] += 1
                results["by_account"][info] = results["by_account"].get(info, 0) + 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "to": to_email,
                    "subject": subject[:50],
                    "error": info,
                })

        # Give detailed summary
        logger.info(
            f"Batch send: {results['sent']}/{results['total']} sent, "
            f"{results['failed']} failed"
        )
        return results

    async def get_pool_status(self) -> Dict[str, Any]:
        status = {
            "total_accounts": len(self._accounts),
            "total_capacity": self.get_total_daily_capacity(),
            "accounts": {},
        }
        for client in self._accounts:
            status["accounts"][client.account.name] = {
                "user": client.account.user,
                "provider": client.account.provider_type,
                "daily_limit": client.account.daily_limit,
                "sent_today": client._sent_today,
                "remaining": client.quota_remaining(),
                "available": client.can_send(),
                "failures": client._consecutive_failures,
                "last_error": client._last_error,
            }
        return status

    def _persist_stats(self):
        """Save daily send counts for crash recovery."""
        try:
            os.makedirs(os.path.dirname(self._stats_file), exist_ok=True)
            stats = {
                str(date.today()): {
                    client.account.name: client._sent_today
                    for client in self._accounts
                }
            }
            with open(self._stats_file, "w") as f:
                json.dump(stats, f)
        except Exception:
            pass

    def _load_persisted_stats(self):
        """Restore previously saved stats (for crash recovery)."""
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file) as f:
                    data = json.load(f)
                today = str(date.today())
                if today in data:
                    account_map = {c.account.name: c for c in self._accounts}
                    for name, count in data[today].items():
                        if name in account_map:
                            account_map[name]._sent_today = count
                    logger.info(f"Restored email rotator stats for {today}")
        except Exception:
            pass

    async def disconnect_all(self):
        for client in self._accounts:
            await client.disconnect()
