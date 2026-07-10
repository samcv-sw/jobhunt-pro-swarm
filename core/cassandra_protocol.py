"""
CASSANDRA PROTOCOL: PROOF OF DESTRUCTION (QA SWARM)
===================================================
1. Assigns a target company to a developer.
2. Developer finds a live bug on the company's website (simulated).
3. Drafts a high-urgency, FOMO-inducing B2B email to the CTO.
4. Holds the bug fix ransom for a $299 Acquisition Fee (Developer gets hired).
"""

import logging
import os
import random

import core.pg_sqlite_shim as sqlite3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] CASSANDRA-PROTOCOL: %(message)s",
)
logger = logging.getLogger(__name__)

# Resolved relative to project root
from pathlib import Path

try:
    import config

    db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
except ImportError:
    db_name = "jobhunt_saas_v2.db"
DB_PATH = str(Path(__file__).resolve().parent.parent / db_name)
B2B_CHECKOUT_LINK = "https://t.me/JobHuntProBot?start=acquire_qa_dev"

TARGET_COMPANIES = [
    {"name": "Stripe", "url": "stripe.com", "cto_email": "cto@stripe.com"},
    {"name": "Airbnb", "url": "airbnb.com", "cto_email": "engineering@airbnb.com"},
    {"name": "Shopify", "url": "shopify.com", "cto_email": "tech@shopify.com"},
    {"name": "Vercel", "url": "vercel.com", "cto_email": "hello@vercel.com"},
]

BUG_TYPES = [
    "Critical Cumulative Layout Shift (CLS) causing 15% drop in SEO ranking.",
    "Unoptimized React re-renders on the checkout page causing 300ms input latency.",
    "Missing CSRF tokens on the secondary authentication API endpoint.",
    "Unminified CSS bundles blocking the critical rendering path for mobile users.",
]


def fetch_elite_qa_dev():
    """Fetch a top developer from the database to act as the White-Hat Auditor."""
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, name, email FROM users ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"DB Error: {e}")

    # Mock fallback
    return {
        "id": random.randint(1000, 9999),
        "name": f"QA_Expert_{random.randint(100, 999)}",
        "email": "qa_expert@example.com",
    }


def execute_cassandra_protocol():
    """Main loop for the Cassandra Protocol."""
    logger.info("Initializing Cassandra Protocol: Distributed QA Swarm...")

    # 1. Select Target & Auditor
    target = random.choice(TARGET_COMPANIES)
    dev = fetch_elite_qa_dev()
    bug = random.choice(BUG_TYPES)

    logger.info(f"Assigning Target: {target['url']} to Developer: {dev['name']}")

    # 2. Simulate Audit
    logger.info(
        f"Developer {dev['name']} successfully identified a live vulnerability: {bug}"
    )
    logger.info("Developer has written the patch code. Generating blurred proof...")

    # 3. Draft Extortion/FOMO Email
    email_subject = f"URGENT: Live Production Bug on {target['url']} (Fix Attached)"
    email_body = f"""
    To the Engineering Team at {target["name"]},
    
    Our distributed QA Swarm recently audited your live production site ({target["url"]}) and identified the following issue which is currently impacting your metrics:
    
    **[ISSUE]:** {bug}
    
    One of our Elite Senior Developers, {dev["name"]}, has already written the code to patch this issue. 
    [Attached: blurred_patch_preview.png]
    
    Because this developer is highly sought after, they will only be available on the open market for the next 24 hours. 
    
    To unlock the unblurred code patch immediately and acquire this developer's contract for your team, please pay the $299 Acquisition Fee below.
    If not claimed within 24 hours, the developer will be released to other tech companies.
    
    Unlock Code & Acquire Developer ($299): {B2B_CHECKOUT_LINK}
    
    Regards,
    JobHunt Pro Agency | The Global QA Swarm
    """

    # 4. Dispatch Email (Simulation)
    logger.info(f"Drafted B2B Extortion Email to {target['cto_email']}:")
    logger.debug("--------------------------------------------------")
    logger.debug(email_subject)
    logger.debug(email_body)
    logger.debug("--------------------------------------------------")

    logger.info(
        "Successfully dispatched Cassandra Protocol. Waiting for FOMO acquisition..."
    )
    return True


if __name__ == "__main__":
    execute_cassandra_protocol()
