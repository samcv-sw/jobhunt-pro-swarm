import asyncio
import logging
import re
import json
import httpx
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GhostAgency:
    """
    PROJECT MIDAS: The Ghost Agency
    Searches the internet for people who recently lost their jobs or are "Open to Work".
    Automatically extracts their emails and sends them a targeted pitch.
    """
    def __init__(self):
        self.search_queries = [
            '"just got laid off" email software engineer',
            '"open to work" looking for new opportunities email',
            'site:linkedin.com "open to work" "gmail.com"',
            'site:twitter.com "looking for my next role" email'
        ]
        self.huggingface_url = "https://user-jobhunt-ai-1.hf.space/api/generate" # Replace with real endpoint

    async def search_leads(self):
        leads = []
        logger.info("🕵️‍♂️ Ghost Agency: Scanning internet for desperate job seekers...")
        
        async with httpx.AsyncClient() as client:
            for query in self.search_queries:
                # Using a free public API proxy for DDG (for demo purposes)
                url = f"https://html.duckduckgo.com/html/?q={query}"
                try:
                    resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        html = resp.text
                        # Simple regex to find emails in the search results
                        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
                        for email in emails:
                            if email not in leads and not email.endswith("duckduckgo.com"):
                                leads.append(email)
                except Exception as e:
                    logger.error(f"Search failed: {e}")
                
                await asyncio.sleep(2) # Be polite to DDG
                
        logger.info(f"🎯 Found {len(leads)} potential leads.")
        return leads

    async def pitch_lead(self, email: str):
        # PROJECT OLYMPUS: Dynamic NOWPayments Invoices
        import httpx
        import os
        
        api_key = os.getenv("NOWPAYMENTS_API_KEY", "3C4BHM5-V7641D9-KHBEJY7-865AFER")
        invoice_url = "https://api.nowpayments.io/v1/invoice"
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "price_amount": 20,
            "price_currency": "usd",
            "order_id": f"jobhunt_{email.split('@')[0]}",
            "order_description": "JobHunt Pro 500 AI Applications",
            "ipn_callback_url": "https://YOUR_HUGGINGFACE_SPACE_URL/api/v1/webhook/nowpayments",
            "success_url": "https://jobhunt-pro.com/success",
            "cancel_url": "https://jobhunt-pro.com/cancel"
        }
        
        checkout_link = "[NOWPAYMENTS_LINK_HERE]"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(invoice_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    checkout_link = resp.json().get("invoice_url", checkout_link)
        except Exception as e:
            logger.error(f"Failed to generate NOWPayments invoice: {e}")
        
        subject = "I am an AI. I can get you hired today."
        pitch_body = f"""
        <p>Hello,</p>
        <p>I noticed you are looking for a job. Finding a job manually is outdated. I am an autonomous AI swarm with 200 nodes, and I can apply to 500 relevant jobs on your behalf in the next 10 minutes. I will write a highly personalized cover letter for every single one.</p>
        <p><b>How to activate me:</b></p>
        <ol>
            <li>Click this secure Crypto Checkout Link to pay $20: <br>
            <a href="{checkout_link}">{checkout_link}</a></li>
            <li>Once payment is confirmed, reply to this email with your CV.</li>
        </ol>
        <p>Once the blockchain confirms your transaction, my 200 nodes will immediately execute your job hunt.</p>
        <p>Best regards,<br>The JobHunt Pro AI Swarm</p>
        """
        logger.info(f"🚀 [OLYMPUS] Sending dynamic crypto invoice to: {email}")
        
        # Real integration: Actually send the email using the rotation engine
        try:
            import qclaw_email_engine
            # Run synchronously since qclaw_email_engine functions are sync
            success = await asyncio.to_thread(qclaw_email_engine.send_one_email, email, subject, pitch_body)
            if success:
                logger.info(f"✅ Email successfully delivered to {email}")
            else:
                logger.error(f"❌ Failed to send email to {email}")
        except Exception as e:
            logger.error(f"❌ Error importing/running QClaw: {e}")

    async def run(self):
        leads = await self.search_leads()
        for lead in leads:
            await self.pitch_lead(lead)
            await asyncio.sleep(1) # Don't spam
        logger.info("✅ Ghost Agency campaign complete.")

if __name__ == "__main__":
    agency = GhostAgency()
    asyncio.run(agency.run())
