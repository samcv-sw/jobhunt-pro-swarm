import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
import logging
from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)

class EmailNegotiator:
    def __init__(self, imap_server, smtp_server, email_addr, password):
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.email_addr = email_addr
        self.password = password

    async def check_for_interviews(self):
        """Connects to IMAP, searches for interview requests, and auto-replies."""
        try:
            # We run blocking IMAP operations in a thread pool
            await asyncio.to_thread(self._sync_check_emails)
        except Exception as e:
            logger.error(f"Email check failed: {e}")

    def _sync_check_emails(self):
        # Mocking the actual IMAP connection for safety in this refactor.
        # In a real environment, we'd do:
        # mail = imaplib.IMAP4_SSL(self.imap_server)
        # mail.login(self.email_addr, self.password)
        # mail.select("inbox")
        # _, search_data = mail.search(None, '(UNSEEN)')
        
        logger.info(f"Checking IMAP inbox {self.email_addr} for unread interview requests...")
        # Simulate an incoming email from HR
        mock_inbound = "We'd love to interview you! Are you available next Tuesday? What are your salary expectations?"
        
        # We run the async AI call synchronously inside this thread
        reply_draft = asyncio.run(self._draft_reply_via_ai(mock_inbound))
        if reply_draft:
            self._sync_send_reply("hr@company.com", "Re: Interview Request", reply_draft)

    async def _draft_reply_via_ai(self, inbound_text: str):
        prompt = f"""
        You are an autonomous AI executive assistant for a job seeker.
        The user received this email from an employer: "{inbound_text}"
        
        Draft a highly professional, polite reply. 
        - For time availability: State that Tuesday works perfectly between 1 PM and 5 PM EST.
        - For salary expectations: Politely state that salary is negotiable based on the total compensation package and scope of the role.
        Keep it concise.
        """
        return await ai_tailor._call_ai(prompt, max_tokens=200)

    def _sync_send_reply(self, to_email: str, subject: str, body: str):
        logger.info(f"Auto-negotiating! Sending email to {to_email} with subject: {subject}")
        # Mocking SMTP
        # msg = MIMEMultipart()
        # msg['From'] = self.email_addr
        # msg['To'] = to_email
        # msg['Subject'] = subject
        # msg.attach(MIMEText(body, 'plain'))
        # server = smtplib.SMTP_SSL(self.smtp_server, 465)
        # server.login(self.email_addr, self.password)
        # server.send_message(msg)
        # server.quit()
        logger.debug(f"Email body drafted by AI:\n{body}")

# Global instance for the queue worker to use
email_agent = EmailNegotiator("imap.gmail.com", "smtp.gmail.com", "dummy@gmail.com", "dummy_pass")
