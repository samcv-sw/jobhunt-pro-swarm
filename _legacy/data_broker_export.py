import sqlite3
import csv
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataBroker:
    """
    PROJECT KRONOS: The Data Broker
    Extracts scraped job data (company names, hiring manager emails, roles) 
    and packages them into highly valuable CSV files for B2B lead selling.
    """
    def __init__(self, db_path="jobhunt_saas_v2.db"):
        self.db_path = db_path
        self.output_dir = "kronos_exports"
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_leads(self):
        logger.info("💎 KRONOS: Mining database for B2B Leads...")
        try:
            conn = sqlite3.connect(self.db_path)
            # We look for jobs that might have an email embedded or associated hiring managers.
            # Since the schema might vary, we simulate pulling the most valuable data.
            # In a real DB, we would query: SELECT company, hr_email, role FROM jobs WHERE hr_email IS NOT NULL
            cursor = conn.cursor()
            
            # For demonstration, we'll extract all jobs and format them as a lead list
            cursor.execute("SELECT id, title, company, location FROM jobs LIMIT 1000")
            jobs = cursor.fetchall()
            
            if not jobs:
                logger.warning("No jobs found in the database to extract.")
                return

            export_file = os.path.join(self.output_dir, "premium_b2b_hiring_leads.csv")
            with open(export_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Job ID", "Role", "Company", "Location", "Estimated HR Email (Format)"])
                
                count = 0
                for job in jobs:
                    # Simulating HR email guessing based on company name
                    company_clean = str(job[2]).lower().replace(" ", "").replace(",", "")
                    if company_clean:
                        hr_email = f"careers@{company_clean}.com"
                    else:
                        hr_email = "hr@unknown.com"
                        
                    writer.writerow([job[0], job[1], job[2], job[3], hr_email])
                    count += 1

            logger.info(f"✅ Successfully packaged {count} B2B Leads into {export_file}")
            logger.info("💰 You can now sell this CSV on Apollo, Gumroad, or to Marketing Agencies for $500+.")
            
        except Exception as e:
            logger.error(f"Failed to extract leads: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    broker = DataBroker()
    broker.extract_leads()
