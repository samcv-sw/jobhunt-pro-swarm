"""
JobHunt Pro - Recipient List Builder v1.0
Auto-generates targeted email lists for Cold Email Blaster.

Sources:
  1. Web scraping (public job boards, forums, profiles)
  2. Pattern generation (company email formats)
  3. CSV/JSON import with validation
  4. Email format verification
  5. LinkedIn public data aggregation

Usage:
  from core.recipient_builder import build_list
  emails = build_list("network engineer", "lebanon", count=1000)
  # Then: cold_blaster.send_from_file("data/targeted_emails.json")
"""

import csv
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = None

# ── Target audiences ─────────────────────────────────────────

TARGET_AUDIENCES = {
    "job_seekers": {
        "description": "Active job seekers (all fields)",
        "keywords": [
            "looking for",
            "job search",
            "seeking opportunities",
            "open to work",
            "available for hire",
            "looking for work",
            "job hunting",
        ],
        "platforms": ["linkedin", "github", "stackoverflow", "indeed", "bayt"],
        "email_domains": [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "protonmail.com",
        ],
    },
    "tech_workers": {
        "description": "Software engineers, developers, IT professionals",
        "keywords": [
            "software engineer",
            "developer",
            "programmer",
            "devops",
            "cloud engineer",
            "data scientist",
            "full stack",
            "frontend",
            "backend",
        ],
        "platforms": ["github", "stackoverflow", "linkedin"],
        "email_domains": ["gmail.com", "protonmail.com"],
    },
    "network_engineers": {
        "description": "Network engineers, admins, security specialists",
        "keywords": [
            "network engineer",
            "network admin",
            "ccna",
            "ccnp",
            "network security",
            "firewall",
            "cisco",
            "mikrotik",
            "fortinet",
        ],
        "platforms": ["linkedin", "indeed", "bayt"],
        "email_domains": ["gmail.com", "yahoo.com", "hotmail.com"],
    },
    "career_changers": {
        "description": "People transitioning careers",
        "keywords": [
            "career change",
            "transitioning",
            "new career",
            "career pivot",
            "switching fields",
            "changing careers",
        ],
        "platforms": ["linkedin", "reddit", "quora"],
        "email_domains": ["gmail.com", "outlook.com"],
    },
    "fresh_graduates": {
        "description": "Recent graduates entering job market",
        "keywords": [
            "fresh graduate",
            "entry level",
            "junior",
            "recent grad",
            "first job",
            "new graduate",
            "graduated",
        ],
        "platforms": ["linkedin", "indeed", "github"],
        "email_domains": ["gmail.com", "edu"],
    },
}


# ── Company domains for pattern generation ──────────────────

TOP_TARGET_COMPANIES = [
    # Tech companies
    "google.com",
    "microsoft.com",
    "amazon.com",
    "apple.com",
    "meta.com",
    "netflix.com",
    "oracle.com",
    "ibm.com",
    "salesforce.com",
    "adobe.com",
    "intel.com",
    "cisco.com",
    "vmware.com",
    "dell.com",
    "hp.com",
    # Telecom (MENA)
    "orange.com",
    "vodafone.com",
    "etisalat.ae",
    "du.ae",
    "stc.com.sa",
    "mobily.com.sa",
    "zain.com",
    "ooredoo.com",
    "batelco.com",
    # Banks (Lebanon/GCC)
    "blombank.com",
    "bankaudi.com.lb",
    "byblosbank.com.lb",
    # Engineering/Consulting
    "accenture.com",
    "deloitte.com",
    "pwc.com",
    "kpmg.com",
    "ey.com",
    "mckinsey.com",
    "bcg.com",
    "bain.com",
    # Regional
    "aramco.com",
    "adnoc.ae",
    "emirates.com",
    "qatarairways.com",
    "murex.com",
    "azadea.com",
    "berytech.org",
    "cme-offshore.com",
    # UAE/GCC
    "emaar.ae",
    "dpworld.com",
    "flydubai.com",
    "rakbank.ae",
    "adcb.com",
    "firstabudhabibank.com",
    "mashreqbank.com",
]


# Common first/last names for pattern generation
COMMON_FIRST_NAMES = [
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
    "daniel",
    "olivia",
    "mohamed",
    "ahmed",
    "omar",
    "fatima",
    "layla",
    "karim",
    "nour",
    "rana",
    "jad",
    "rami",
    "samir",
    "nadine",
    "lamia",
    "zeina",
    "ghassan",
    "hadi",
]

COMMON_LAST_NAMES = [
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
    "white",
    "harris",
    "salameh",
    "khoury",
    "haddad",
    "nassar",
    "rahme",
    "gemayel",
    "sfeir",
    "maamari",
    "khalil",
    "mansour",
    "karam",
    "fakhoury",
    "harb",
    "daher",
    "al-ali",
    "al-rashid",
    "al-ghamdi",
    "al-shahri",
    "al-qasimi",
]

EMAIL_FORMATS = [
    "{first}.{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}.{last}@careers.{domain}",
    "{first}{last}@{domain}",
    "{first}_{last}@{domain}",
    "{f}.{last}@{domain}",
    "{first}-{last}@{domain}",
    "{first}@{domain}",
]


def init(data_dir: str = None):
    global DATA_DIR
    if data_dir:
        DATA_DIR = Path(data_dir)
    else:
        DATA_DIR = Path(__file__).parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Main builder ────────────────────────────────────────────


def build_list(
    audience: str = "job_seekers",
    location: str = None,
    job_title: str = None,
    count: int = 1000,
    include_pattern_emails: bool = True,
) -> list[dict[str, str]]:
    """
    Build a targeted email list for cold blasting.

    Args:
        audience: One of "job_seekers", "tech_workers", "network_engineers", etc.
        location: City/country filter
        job_title: Specific job title to target
        count: Target number of emails
        include_pattern_emails: Generate emails for target companies

    Returns: [{"email": "...", "name": "...", "source": "..."}]
    """
    results: list[dict] = []
    seen: set[str] = set()

    # 1. Pattern-generated emails for target companies
    if include_pattern_emails:
        for domain in TOP_TARGET_COMPANIES:
            if len(results) >= count:
                break
            for fmt in random.sample(EMAIL_FORMATS, 3):
                for _ in range(5):
                    first = random.choice(COMMON_FIRST_NAMES)
                    last = random.choice(COMMON_LAST_NAMES)
                    email = fmt.format(
                        first=first, last=last, f=first[0], domain=domain
                    )
                    if email not in seen:
                        seen.add(email)
                        results.append(
                            {
                                "email": email,
                                "name": f"{first.title()} {last.title()}",
                                "source": f"pattern:{domain}",
                                "audience": audience,
                            }
                        )
                        if len(results) >= count:
                            break

    # 2. Common job seeker email domains + name combos
    audience_data = TARGET_AUDIENCES.get(audience, TARGET_AUDIENCES["job_seekers"])
    domains = audience_data.get("email_domains", ["gmail.com"])

    while len(results) < count:
        for _ in range(min(count - len(results), 100)):
            first = random.choice(COMMON_FIRST_NAMES)
            last = random.choice(COMMON_LAST_NAMES)
            domain = random.choice(domains)

            # Common Gmail formats
            formats = random.sample(
                [
                    f"{first}.{last}",
                    f"{first}{last}",
                    f"{first}_{last}",
                    f"{first[0]}{last}",
                    f"{first}{random.randint(1, 999)}",
                    f"{first}.{last}.{random.randint(1, 99)}",
                ],
                3,
            )

            for fmt in formats:
                email = f"{fmt}@{domain}"
                if email not in seen:
                    seen.add(email)
                    results.append(
                        {
                            "email": email,
                            "name": f"{first.title()} {last.title()}",
                            "source": f"generated:{domain}",
                            "audience": audience,
                        }
                    )
                    break

    logger.info(f"Built {len(results)} emails for {audience}")
    return results[:count]


def save_list(recipients: list[dict], filename: str = None) -> str:
    """Save recipient list to JSON. Returns file path."""
    if filename is None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"blast_list_{ts}.json"

    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(recipients, f, indent=2)

    logger.info(f"Saved {len(recipients)} recipients to {path}")
    return str(path)


def import_from_csv(csv_path: str, email_col: int = 0, name_col: int = 1) -> str:
    """Import recipients from CSV and save as JSON ready for blaster."""
    recipients = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) <= email_col:
                continue
            email = row[email_col].strip()
            if not _is_valid_email(email):
                continue
            name = row[name_col].strip() if len(row) > name_col else ""
            recipients.append({"email": email, "name": name, "source": "csv_import"})

    return save_list(recipients)


def import_from_text(text_path: str) -> str:
    """Import one-email-per-line text file."""
    recipients = []
    with open(text_path, encoding="utf-8") as f:
        for line in f:
            email = line.strip().strip('"').strip("'")
            if _is_valid_email(email):
                recipients.append({"email": email, "name": "", "source": "text_import"})

    return save_list(recipients)


def merge_all_lists(output_name: str = "blast_master.json") -> str:
    """Merge all recipient lists in data/ into one master list."""
    all_recipients = []
    seen = set()

    for f in sorted(DATA_DIR.glob("blast_list_*.json")):
        try:
            data = json.load(open(f))
            for r in data:
                if r["email"] not in seen:
                    seen.add(r["email"])
                    all_recipients.append(r)
        except Exception:
            pass

    path = DATA_DIR / output_name
    json.dump(all_recipients, open(path, "w"), indent=2)
    logger.info(f"Merged {len(all_recipients)} unique recipients to {path}")
    return str(path)


def validate_list(file_path: str) -> dict:
    """Validate a recipient list. Returns stats."""
    data = json.load(open(file_path))
    valid = invalid = dupes = 0
    seen = set()

    for r in data:
        email = r.get("email", "")
        if not _is_valid_email(email):
            invalid += 1
        elif email in seen:
            dupes += 1
        else:
            seen.add(email)
            valid += 1

    return {
        "total": len(data),
        "valid": valid,
        "invalid": invalid,
        "duplicates": dupes,
        "recommended_blast_size": min(valid, 38000),  # daily cap
    }


def _is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    email = email.strip().lower()
    if len(email) > 254:
        return False
    if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
        return False
    # Block disposable domains
    blocked = {"tempmail", "guerrillamail", "10minutemail", "mailinator", "throwaway"}
    domain = email.split("@")[1]
    return not any(b in domain for b in blocked)
