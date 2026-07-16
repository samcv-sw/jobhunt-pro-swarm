import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

# Fallback SECRET_KEY to prevent web.shared from raising RuntimeError
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "jobhunt-pro-cli-ephemeral-secret-key"

import config
from core.campaign_runner import run_campaign
from web.shared import get_db


async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_campaign_cli.py <campaign_id> [company_limit]")
        sys.exit(1)
    campaign_id = sys.argv[1]
    company_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print(f"Starting campaign {campaign_id} with limit {company_limit}...")
    result = await run_campaign(campaign_id, get_db, config, company_limit=company_limit)
    print(f"Campaign finished: {result}")

if __name__ == "__main__":
    asyncio.run(main())
