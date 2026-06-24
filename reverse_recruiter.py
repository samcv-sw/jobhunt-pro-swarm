import sqlite3
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReverseRecruiter:
    """
    PROJECT APOTHEOSIS: The Reverse Recruiter
    Scrapes companies that are hiring (from the local DB) and emails the HR managers,
    offering to sell them a pre-vetted list of candidates for a flat crypto fee.
    """
    def __init__(self, db_path="jobhunt_saas_v2.db"):
        self.db_path = db_path
        
    def get_hiring_companies(self):
        # We find companies that have posted recent jobs
        logger.info("🏢 APOTHEOSIS: Scanning for companies actively hiring...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # In a real scenario, we'd only pick companies where we guessed the HR email
            cursor.execute("SELECT DISTINCT company FROM jobs LIMIT 20")
            companies = [row[0] for row in cursor.fetchall() if row[0]]
            return companies
        except Exception as e:
            logger.error(f"DB Error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()

    async def pitch_company(self, company_name: str):
        company_clean = company_name.lower().replace(" ", "").replace(",", "")
        hr_email = f"careers@{company_clean}.com"
        
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
            "price_amount": 100,
            "price_currency": "usd",
            "order_id": f"b2b_{company_clean}",
            "order_description": f"50 Pre-Vetted Engineers CVs for {company_name}",
            "ipn_callback_url": f"{os.getenv('SITE_URL', 'https://jhfguf.pythonanywhere.com')}/api/v1/webhook/nowpayments",
            "success_url": f"{os.getenv('SITE_URL', 'https://jhfguf.pythonanywhere.com')}/payment/success",
            "cancel_url": f"{os.getenv('SITE_URL', 'https://jhfguf.pythonanywhere.com')}/payment/cancel"
        }
        
        checkout_link = "[NOWPAYMENTS_LINK_HERE]"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(invoice_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    checkout_link = resp.json().get("invoice_url", checkout_link)
        except Exception as e:
            logger.error(f"Failed to generate NOWPayments invoice: {e}")
            
        subject = f"Pre-Vetted Software Engineers for {company_name}"
        pitch_body = f"""
        <p>Hello {company_name} Hiring Team,</p>
        <p>I see you are actively hiring. Recruiting is expensive, but I have a shortcut for you.</p>
        <p>I operate a highly exclusive talent database. I currently have 50 pre-vetted, highly qualified software engineers actively looking for a role similar to what you are offering.</p>
        <p>Instead of paying a recruiter $10,000, you can unlock this exclusive candidate list instantly.</p>
        <p><b>How to unlock the CV Database:</b></p>
        <ol>
            <li>Click here to securely pay $100 via Crypto checkout: <br>
            <a href="{checkout_link}">{checkout_link}</a></li>
        </ol>
        <p>Upon confirmation, our automated system will instantly email you the secure link to download the 50 CVs.</p>
        <p>Best regards,<br>The JobHunt Pro Talent Network</p>
        """
        
        logger.info(f"💼 [OLYMPUS] Sending dynamic B2B Crypto pitch to: {hr_email}")
        
        try:
            import qclaw_email_engine
            # Run synchronously since qclaw_email_engine functions are sync
            success = await asyncio.to_thread(qclaw_email_engine.send_one_email, hr_email, subject, pitch_body)
            if success:
                logger.info(f"✅ B2B Pitch delivered to {hr_email}")
            else:
                logger.error(f"❌ Failed to send B2B Pitch to {hr_email}")
        except Exception as e:
            logger.error(f"❌ Error importing/running QClaw: {e}")

    async def run(self):
        companies = self.get_hiring_companies()
        for company in companies:
            await self.pitch_company(company)
            await asyncio.sleep(2) # Avoid spam
        logger.info("✅ Reverse Recruiter campaign complete.")

if __name__ == "__main__":
    recruiter = ReverseRecruiter()
    asyncio.run(recruiter.run())
