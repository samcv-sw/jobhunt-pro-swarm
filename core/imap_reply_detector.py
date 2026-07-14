"""
IMAP Reply Detector — IMP-227
Polls IMAP mailboxes for replies to sent job applications.
Stores matched replies in the ApplicationReply model.
"""
import email
import imaplib
import logging
from datetime import UTC, datetime, timedelta
from email.header import decode_header

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — IMP-159: named constants instead of magic numbers
# ---------------------------------------------------------------------------
DEFAULT_POLL_HOURS: int = 24          # How far back to search for replies
IMAP_TIMEOUT_SECONDS: int = 30        # IMAP connection timeout
MAX_MESSAGES_PER_POLL: int = 200      # Cap messages scanned per poll run
REPLY_POLL_INTERVAL_MINUTES: int = 30  # Celery task interval


def decode_email_header(raw: str) -> str:
    """Safely decode an email header that may be encoded.

    Args:
        raw: Raw email header string (may be RFC 2047 encoded).

    Returns:
        Decoded string in UTF-8 or latin-1.
    """
    parts = decode_header(raw or "")
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, TypeError):
                decoded.append(part.decode("latin-1", errors="replace"))
        else:
            decoded.append(str(part))
    return " ".join(decoded)


def poll_replies(
    imap_host: str,
    imap_user: str,
    imap_pass: str,
    since_hours: int = DEFAULT_POLL_HOURS,
    sent_message_ids: set | None = None,
) -> list[dict]:
    """Poll an IMAP mailbox for replies to sent job applications — IMP-227.

    Searches for emails with In-Reply-To or References headers matching
    any of the provided sent message IDs.

    Args:
        imap_host: IMAP server hostname (e.g., 'imap.gmail.com').
        imap_user: IMAP login username.
        imap_pass: IMAP login password.
        since_hours: Number of hours to look back (default: 24).
        sent_message_ids: Set of Message-ID strings from sent applications.
            If None, returns all recent replies.

    Returns:
        List of reply dicts with keys: from, subject, date, in_reply_to, message_id.
    """
    replies = []
    since_dt = datetime.now(UTC) - timedelta(hours=since_hours)
    since_str = since_dt.strftime("%d-%b-%Y")

    try:
        mail = imaplib.IMAP4_SSL(imap_host, timeout=IMAP_TIMEOUT_SECONDS)
        mail.login(imap_user, imap_pass)
        mail.select("INBOX")

        _, msg_nums = mail.search(None, f'(SINCE "{since_str}")')
        if not msg_nums or not msg_nums[0]:
            mail.logout()
            return replies

        num_list = msg_nums[0].split()
        # Scan most recent first; cap at MAX_MESSAGES_PER_POLL
        for num in num_list[-MAX_MESSAGES_PER_POLL:]:
            try:
                _, msg_data = mail.fetch(num, "(RFC822.HEADER)")
                if not msg_data or not msg_data[0]:
                    continue
                raw_header = msg_data[0][1] if isinstance(msg_data[0], tuple) else b""
                msg = email.message_from_bytes(raw_header)

                in_reply_to = msg.get("In-Reply-To", "").strip()
                references = msg.get("References", "").strip()
                message_id = msg.get("Message-ID", "").strip()

                # Check if this is a reply to one of our sent messages
                is_reply = False
                if sent_message_ids:
                    for sid in sent_message_ids:
                        if sid in in_reply_to or sid in references:
                            is_reply = True
                            break
                else:
                    # No filter: collect all recent replies
                    is_reply = bool(in_reply_to or references)

                if is_reply:
                    replies.append({
                        "from": decode_email_header(msg.get("From", "")),
                        "subject": decode_email_header(msg.get("Subject", "")),
                        "date": msg.get("Date", ""),
                        "in_reply_to": in_reply_to,
                        "message_id": message_id,
                    })
            except Exception as inner_e:
                logger.debug(f"[IMAPReply] Error parsing message {num}: {inner_e}")
                continue

        mail.logout()
    except imaplib.IMAP4.error as e:
        logger.error(f"[IMAPReply] IMAP authentication/connection error: {e}")
    except OSError as e:
        logger.error(f"[IMAPReply] IMAP network error connecting to {imap_host}: {e}")
    except Exception as e:
        logger.error(f"[IMAPReply] Unexpected error during poll: {e}")

    logger.info(f"[IMAPReply] Found {len(replies)} replies in the last {since_hours}h")
    return replies


def store_replies(replies: list[dict], application_id: str = "") -> int:
    """Persist detected replies to the database — IMP-227.

    Args:
        replies: List of reply dicts from poll_replies().
        application_id: Optional application ID to associate replies with.

    Returns:
        Number of replies stored.
    """
    stored = 0
    for reply in replies:
        try:
            # Use SQLite shim for synchronous writes from Celery context
            import config
            import core.pg_sqlite_shim as sqlite3
            db_path = getattr(config, "DB_PATH", "data/jobhunt_saas_v2.db")
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS application_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT,
                    reply_from TEXT,
                    reply_subject TEXT,
                    message_id TEXT UNIQUE,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                """INSERT OR IGNORE INTO application_replies
                   (application_id, reply_from, reply_subject, message_id)
                   VALUES (?, ?, ?, ?)""",
                (
                    application_id,
                    reply.get("from", ""),
                    reply.get("subject", ""),
                    reply.get("message_id", ""),
                )
            )
            conn.commit()
            conn.close()
            stored += 1
        except Exception as e:
            logger.error(f"[IMAPReply] Failed to store reply: {e}")
    return stored
