import os
import requests
import sqlite3
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "leads.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            github_username TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def search_github():
    # We search for users with bios indicating they want a job
    queries = [
        '"open to work" type:user',
        '"looking for a job" type:user',
        '"seeking new opportunities" type:user',
        '"hire me" type:user',
        '"looking for software engineering roles" type:user'
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    added_count = 0

    for query in queries:
        logger.info(f"Searching GitHub for: {query}")
        # Page 1 to 5 to avoid deep pagination rate limits
        for page in range(1, 6):
            url = f"https://api.github.com/search/users?q={requests.utils.quote(query)}&page={page}&per_page=30"
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 403:
                    logger.warning("GitHub API rate limit hit. Sleeping for 60 seconds...")
                    time.sleep(60)
                    continue
                elif resp.status_code != 200:
                    break
                
                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break
                
                for item in items:
                    username = item.get("login")
                    # Fetch user profile to get email
                    user_url = f"https://api.github.com/users/{username}"
                    user_resp = requests.get(user_url, headers=headers)
                    if user_resp.status_code == 200:
                        user_data = user_resp.json()
                        email = user_data.get("email")
                        name = user_data.get("name") or username
                        
                        if email:
                            try:
                                cursor.execute(
                                    "INSERT INTO leads (name, email, github_username) VALUES (?, ?, ?)",
                                    (name, email, username)
                                )
                                conn.commit()
                                logger.info(f"✅ Found Lead: {name} ({email})")
                                added_count += 1
                            except sqlite3.IntegrityError:
                                # Email already exists
                                pass
                    time.sleep(1) # Sleep to respect API rate limits
            except Exception as e:
                logger.error(f"Error fetching from GitHub: {e}")
            
            time.sleep(2) # Sleep between pages

    conn.close()
    logger.info(f"Scraping cycle complete. Added {added_count} new leads.")

if __name__ == "__main__":
    init_db()
    logger.info("🕷️ Starting Lead Generator (GitHub Scout)...")
    search_github()
