"""
Cloud Keep-Alive Script (24/7 Uptime)
=====================================
This script is designed to run in the background (e.g., as a PythonAnywhere Always-On task,
or on any local machine/server) to ensure the web application never goes to sleep.

It will ping the /ping endpoint every 4 minutes.
"""
import time
import urllib.request
import urllib.error
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - KEEPALIVE - %(levelname)s - %(message)s")
logger = logging.getLogger("keepalive")

TARGET_URL = "https://jhfguf.pythonanywhere.com/ping"
PING_INTERVAL_SECONDS = 4 * 60  # 4 minutes

def run_loop():
    logger.info(f"Starting Keep-Alive loop for {TARGET_URL} every {PING_INTERVAL_SECONDS} seconds.")
    while True:
        try:
            req = urllib.request.Request(TARGET_URL, headers={'User-Agent': 'JobHuntPro-KeepAlive/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Ping successful -> App is awake.")
                else:
                    logger.warning(f"Ping returned unexpected status: {response.status}")
        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
        
        # Sleep until the next interval
        time.sleep(PING_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        run_loop()
    except KeyboardInterrupt:
        logger.info("Keep-Alive loop stopped.")
