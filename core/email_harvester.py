"""
JobHunt Pro - Email Harvester v1.0
Multi-source email harvesting for cold blaster campaigns.

Sources:
  1. Local files (CSV, JSON, TXT)
  2. GitHub public profiles (looking-for-work)
  3. LinkedIn public data (via search dorks)
  4. Job board scraping (public listings)
  5. Pattern generation for target companies
"""

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────
HARVEST_DIR = None  # set by init()

# Common email patterns for target companies
EMAIL_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{first}.{last}@careers.{domain}",
    "{first}@{domain}",
    "{f}.{last}@{domain}",
    "{first}_{last}@{domain}",
    "{first}-{last}@{domain}",
]

# Target domains for job seekers
JOB_SEEKER_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "protonmail.com",
    "mail.com",
    "aol.com",
    "icloud.com",
]


def init(data_dir: str | None = None):
    """Initialize harvester."""
    global HARVEST_DIR
    if data_dir:
        HARVEST_DIR = Path(data_dir)
    else:
        HARVEST_DIR = Path(__file__).parent.parent / "data"
    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"EmailHarvester initialized at {HARVEST_DIR}")


def load_from_csv(
    csv_path: str, email_col: int = 0, name_col: int = 1
) -> list[dict[str, str]]:
    """Load emails from CSV file."""
    import csv

    recipients = []

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            email = row[email_col].strip() if len(row) > email_col else ""
            if not _is_valid_email(email):
                continue
            name = row[name_col].strip() if len(row) > name_col else ""
            recipients.append({"email": email, "name": name})

    logger.info(f"CSV: {len(recipients)} emails from {csv_path}")
    return recipients


def load_from_json(json_path: str) -> list[dict[str, str]]:
    """Load emails from JSON file [{"email":..., "name":...}]."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    recipients = []
    for r in data:
        email = r.get("email", "")
        if _is_valid_email(email):
            recipients.append({"email": email, "name": r.get("name", "")})

    logger.info(f"JSON: {len(recipients)} emails from {json_path}")
    return recipients


def load_from_txt(txt_path: str) -> list[dict[str, str]]:
    """Load emails from plain text (one per line)."""
    recipients = []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            email = line.strip()
            if _is_valid_email(email):
                recipients.append({"email": email, "name": ""})

    logger.info(f"TXT: {len(recipients)} emails from {txt_path}")
    return recipients


def harvest_github_job_seekers(min_stars: int = 0) -> list[dict[str, str]]:
    """
    Harvest GitHub users who are looking for work.
    Searches public profiles with "looking for work" in bio.
    NOTE: Requires network access. Uses GitHub API (rate limited, no auth needed for public).
    """
    recipients = []
    try:
        import requests

        # Search for users with "looking for" or "open to work" in bio
        queries = [
            "looking for work type:user",
            "open to work type:user",
            "seeking opportunities type:user",
            "looking for job type:user",
            "#OpenToWork type:user",
        ]

        for query in queries[:3]:  # limit to avoid rate limits
            try:
                r = requests.get(
                    "https://api.github.com/search/users",
                    params={"q": query, "per_page": 30},
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=10,
                )
                if r.status_code == 200:
                    users = r.json().get("items", [])
                    for user in users:
                        # Get user details for email
                        detail_r = requests.get(
                            user["url"],
                            headers={"Accept": "application/vnd.github.v3+json"},
                            timeout=10,
                        )
                        if detail_r.status_code == 200:
                            detail = detail_r.json()
                            email = detail.get("email", "")
                            if _is_valid_email(email):
                                recipients.append(
                                    {
                                        "email": email,
                                        "name": detail.get("name", user["login"]),
                                    }
                                )
                time.sleep(2)  # respect rate limits
            except Exception:
                continue

    except ImportError:
        logger.warning("requests not available for GitHub harvest")
    except Exception as e:
        logger.error(f"GitHub harvest error: {e}")

    logger.info(f"GitHub: harvested {len(recipients)} emails")
    return recipients


def generate_emails_for_company(
    company_domain: str, first_names: list[str] = None, last_names: list[str] = None
) -> list[dict[str, str]]:
    """
    Generate email address candidates for a company using common patterns.

    Args:
        company_domain: e.g. "murex.com"
        first_names: list of common first names
        last_names: list of common last names

    Returns list of {"email": candidate, "name": "First Last"}
    """
    if first_names is None:
        first_names = [
            "john",
            "jane",
            "mike",
            "sarah",
            "david",
            "lisa",
            "robert",
            "maria",
            "james",
            "anna",
            "alex",
            "emma",
            "chris",
            "sophia",
        ]
    if last_names is None:
        last_names = [
            "smith",
            "johnson",
            "williams",
            "brown",
            "jones",
            "miller",
            "davis",
            "wilson",
            "anderson",
            "taylor",
            "thomas",
            "jackson",
        ]

    candidates = []
    for first in first_names:
        for last in last_names:
            for pattern in EMAIL_PATTERNS:
                f = first.lower()
                l = last.lower()
                fi = f[0]

                email = pattern.format(first=f, last=l, f=fi, domain=company_domain)
                name = f"{first.title()} {last.title()}"
                candidates.append(
                    {"email": email, "name": name, "company": company_domain}
                )

    logger.info(f"Generated {len(candidates)} email candidates for {company_domain}")
    return candidates


def load_all_from_directory(dir_path: str) -> list[dict[str, str]]:
    """Load all recipient files from a directory (CSV, JSON, TXT)."""
    all_recipients = []
    d = Path(dir_path)

    for f in sorted(d.iterdir()):
        try:
            if f.suffix == ".csv":
                all_recipients.extend(load_from_csv(str(f)))
            elif f.suffix == ".json":
                all_recipients.extend(load_from_json(str(f)))
            elif f.suffix == ".txt":
                all_recipients.extend(load_from_txt(str(f)))
        except Exception as e:
            logger.warning(f"Skipping {f}: {e}")

    # Deduplicate by email
    seen = set()
    unique = []
    for r in all_recipients:
        if r["email"] not in seen:
            seen.add(r["email"])
            unique.append(r)

    logger.info(
        f"Directory load: {len(unique)} unique from {len(all_recipients)} total"
    )
    return unique


def save_recipients(
    recipients: list[dict[str, str]], filename: str = "harvested_emails.json"
):
    """Save harvested emails to JSON for later blasting."""
    path = HARVEST_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(recipients, f, indent=2)
    logger.info(f"Saved {len(recipients)} recipients to {path}")
    return str(path)


def _is_valid_email(email: str) -> bool:
    """Basic email validation."""
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return False
    # Strip common noise
    email = email.strip().strip('"').strip("'")
    if len(email) > 254:
        return False
    # Basic regex
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))
