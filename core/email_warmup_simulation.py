import random
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core import hotmail_pool

logger = logging.getLogger(__name__)

CONVERSATION_TEMPLATES = [
    {
        "subject": "Quick question regarding the onboarding documentation",
        "body": "Hey there,\n\nDid you get a chance to look at the new setup guides we published yesterday? Let me know if you spot any gaps.\n\nBest regards,\nJobHunt Collaborator"
    },
    {
        "subject": "Follow-up: Weekly sync timing check",
        "body": "Hi,\n\nAre we still on for our sync at 3 PM today? Let me know if we need to push it back by an hour.\n\nThanks,\nProject Lead"
    },
    {
        "subject": "Draft architecture proposal for review",
        "body": "Hello,\n\nI've uploaded the draft architecture document to our shared workspace. Please review the database scaling section when you get a moment.\n\nRegards,\nSystems Engineer"
    },
    {
        "subject": "Notes from the marketing alignment meeting",
        "body": "Hi team,\n\nHere are the key takeaways from today's alignment meeting. We need to finalize the campaign timeline by Thursday.\n\nTalk soon,\nMarketing Coordinator"
    }
]


async def run_warmup_tick() -> bool:
    """Selects two random active Hotmail accounts from the pool and sends a
    simulated friendly conversational email from one to the other.
    This maintains account warming and boosts sender reputation.
    """
    try:
        # Load the Hotmail accounts
        accounts = hotmail_pool.load_pool()
        active_accounts = [a for a in accounts if not a.get("dead", False) and a.get("email")]

        if len(active_accounts) < 2:
            logger.warning("[WARMUP-SIMULATION] Insufficient active accounts in pool to simulate exchange.")
            return False

        # Pick two unique accounts
        sender_acct = random.choice(active_accounts)
        receiver_acct = random.choice(active_accounts)
        while receiver_acct["email"] == sender_acct["email"]:
            receiver_acct = random.choice(active_accounts)

        # Pick a random template
        template = random.choice(CONVERSATION_TEMPLATES)

        # Build the MIME message format required by hotmail_pool.send_email_sync
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_acct["email"]
        msg["To"] = receiver_acct["email"]
        msg["Subject"] = template["subject"]
        msg.attach(MIMEText(template["body"], "plain", "utf-8"))

        logger.info(
            f"[WARMUP-SIMULATION] Simulating email exchange: "
            f"Sender={sender_acct['email']} -> Receiver={receiver_acct['email']}"
        )

        # Under the hood, hotmail_pool.send_email_sync rotates and picks get_account()
        # To force it to send from our selected sender_acct, we can temporarily patch
        # get_account to return sender_acct.
        original_get_account = hotmail_pool.get_account
        hotmail_pool.get_account = lambda *args, **kwargs: sender_acct

        try:
            # Execute the send
            success, status, sender_email = hotmail_pool.send_email_sync(
                receiver_acct["email"],
                msg.as_string()
            )
        finally:
            # Restore original function
            hotmail_pool.get_account = original_get_account

        if success:
            logger.info(f"[WARMUP-SIMULATION] Simulated exchange completed successfully: {status}")
            return True
        else:
            logger.warning(f"[WARMUP-SIMULATION] Simulated exchange failed: {status}")
            return False

    except Exception as e:
        logger.error(f"[WARMUP-SIMULATION] Exception during warmup simulation tick: {e}")
        return False
