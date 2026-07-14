import os
import time
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dns_failover")

# Configurations from environment variables
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "mock_cloudflare_api_token")
CF_ZONE_ID = os.getenv("CF_ZONE_ID", "mock_zone_id_123")
CF_RECORD_ID = os.getenv("CF_RECORD_ID", "mock_record_id_456")

PRIMARY_URL = os.getenv("PRIMARY_URL", "https://jhfguf.pythonanywhere.com/api/v2/cloud-tick/status")
PRIMARY_CNAME_VALUE = os.getenv("PRIMARY_CNAME_VALUE", "jhfguf.pythonanywhere.com")
BACKUP_CNAME_VALUE = os.getenv("BACKUP_CNAME_VALUE", "jobhuntpro-backup.huggingface.co")

POLL_INTERVAL_SECONDS = 30
MAX_FAILURES_BEFORE_SWITCH = 2


def check_primary_health() -> bool:
    """Checks if the primary app region is healthy."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(PRIMARY_URL)
            if resp.status_code == 200:
                return True
            logger.warning(f"Primary region returned status code: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Primary health check request failed: {e}")
    return False


def update_cloudflare_dns(target_cname: str) -> bool:
    """Updates the Cloudflare DNS CNAME record to the target value."""
    if CF_API_TOKEN == "mock_cloudflare_api_token":
        logger.info(f"[MOCK CF API] Successfully updated DNS CNAME record to: {target_cname}")
        return True

    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{CF_RECORD_ID}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "type": "CNAME",
        "name": "@",
        "content": target_cname,
        "ttl": 60,  # 1 minute low TTL for fast failover
        "proxied": True
    }

    try:
        with httpx.Client() as client:
            resp = client.put(url, json=payload, headers=headers)
            if resp.status_code == 200:
                logger.info(f"Cloudflare DNS successfully updated to: {target_cname}")
                return True
            logger.error(f"Cloudflare API failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.error(f"Failed to connect to Cloudflare API: {e}")
    return False


def run_failover_loop():
    """Main loop checking health and performing failover/failback."""
    logger.info("Starting Multi-region DNS Failover Monitor...")
    logger.info(f"Primary: {PRIMARY_CNAME_VALUE} | Backup: {BACKUP_CNAME_VALUE}")

    failures = 0
    current_active = "primary"

    while True:
        is_healthy = check_primary_health()

        if is_healthy:
            failures = 0
            if current_active == "backup":
                logger.info("Primary region is back online! Performing Failback to primary...")
                if update_cloudflare_dns(PRIMARY_CNAME_VALUE):
                    current_active = "primary"
        else:
            failures += 1
            logger.warning(f"Primary health check failure count: {failures}/{MAX_FAILURES_BEFORE_SWITCH}")
            if failures >= MAX_FAILURES_BEFORE_SWITCH and current_active == "primary":
                logger.error("Primary region has gone down! Triggering Failover to backup region...")
                if update_cloudflare_dns(BACKUP_CNAME_VALUE):
                    current_active = "backup"

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    # If running in script mode directly, run check once or start loop
    if os.getenv("RUN_ONCE"):
        health = check_primary_health()
        logger.info(f"Single check complete. Health: {health}")
    else:
        run_failover_loop()
