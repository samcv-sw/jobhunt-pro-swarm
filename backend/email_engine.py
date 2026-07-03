import os
import json
import logging
import random
import asyncio
import smtplib
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)

class RotatingEmailSender:
    def __init__(self, credentials_path: str = "gmail_accounts.json"):
        self.credentials_path = credentials_path
        self.accounts = self._load_accounts()
        self.current_index = 0

    def _load_accounts(self) -> list:
        """Loads email credentials from a local JSON file securely."""
        try:
            # We expect a JSON file like [{"email": "...", "password": "..."}, ...]
            path = Path(__file__).parent.parent / self.credentials_path
            if path.exists():
                with open(path, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Credentials file {self.credentials_path} not found. Running in DRY RUN mode.")
                return []
        except Exception as e:
            logger.error(f"Failed to load email accounts: {e}")
            return []

    def _get_next_account(self) -> dict:
        """Round-robin selection of the next available email account."""
        if not self.accounts:
            return None
        
        account = self.accounts[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.accounts)
        return account

    async def send_email(self, to_email: str, subject: str, body: str):
        """
        Sends an email. Propagates exceptions so that the caller (e.g. a Celery task) can handle retries.
        """
        account = self._get_next_account()
        
        if not account:
            logger.info(f"[DRY RUN] Would send email to {to_email} with subject: {subject}")
            return

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = account['email']
        msg['To'] = to_email
        msg.set_content(body)

        logger.info(f"Attempting to send email via {account['email']}")
        # Execute SMTP sending in a thread pool to avoid blocking the async event loop
        await asyncio.to_thread(self._sync_send_smtp, account, msg)
        logger.info(f"Successfully sent email to {to_email}")

    def _sync_send_smtp(self, account: dict, msg: EmailMessage):
        """Synchronous SMTP logic to be run in a thread pool."""
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(account['email'], account['password'])
            smtp.send_message(msg)
