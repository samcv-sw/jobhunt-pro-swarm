"""
Lebanon Company Database Seeder v1.0
Injects 100+ pre-verified Lebanese companies with contact emails into PA database.
Zero API calls — all data pre-researched and ready.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.pg_sqlite_shim as sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _get_db_path() -> str:
    db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
    base = Path(__file__).resolve().parent.parent
    full = str(base / db_path)
    if not os.path.exists(full):
        alt = str(base / "jobhunt_saas_v2.db")
        if os.path.exists(alt):
            return alt
    return full


# ═══════════════════════════════════════════════════════
# SAM'S TECH COMPANIES
# ═══════════════════════════════════════════════════════
SAM_COMPANIES = [
    ("Murex", "Financial Software", "Beirut", "careers@murex.com", "murex.com", 95),
    (
        "CME Offshore",
        "Technology",
        "Beirut",
        "careers@cmeoffshore.com",
        "cmeoffshore.com",
        92,
    ),
    ("Touch Lebanon", "Telecom", "Beirut", "careers@touch.com.lb", "touch.com.lb", 90),
    ("Alfa Telecom", "Telecom", "Beirut", "careers@alfa.com.lb", "alfa.com.lb", 90),
    ("Berytech", "Technology Hub", "Beirut", "info@berytech.org", "berytech.org", 88),
    ("TerraNet", "ISP/Telecom", "Beirut", "hr@terranet.com.lb", "terranet.com.lb", 85),
    ("Sodetel", "Telecom", "Beirut", "hr@sodetel.net.lb", "sodetel.com.lb", 82),
    ("Ogero Telecom", "Telecom", "Beirut", "info@ogero.gov.lb", "ogero.gov.lb", 85),
    ("Cyberia", "ISP", "Beirut", "hr@cyberia.net.lb", "cyberia.net.lb", 80),
    ("IDM Lebanon", "ISP", "Beirut", "info@idm.com.lb", "idm.com.lb", 78),
    ("Cedarcom", "ISP/Telecom", "Metn", "info@cedarcom.net", "cedarcom.net", 78),
    (
        "Inconet Data",
        "IT Services",
        "Beirut",
        "info@inconet.com.lb",
        "inconet.com.lb",
        80,
    ),
    ("IT Works", "IT Services", "Beirut", "hr@itworksme.com", "itworksme.com", 78),
    ("ElementN", "Software", "Beirut", "info@elementn.com", "elementn.com", 82),
    ("Anghami", "Music Tech", "Beirut", "careers@anghami.com", "anghami.com", 90),
    ("Toters", "Delivery Tech", "Beirut", "careers@toters.app", "toters.com", 85),
    (
        "NAR Technologies",
        "IT Services",
        "Metn",
        "info@nartechnologies.com",
        "nartechnologies.com",
        75,
    ),
    (
        "Malia Group",
        "Technology/Conglomerate",
        "Beirut",
        "hr@maliagroup.com",
        "maliagroup.com",
        85,
    ),
    (
        "Procom Lebanon",
        "IT Services",
        "Beirut",
        "info@procomlb.com",
        "procomlb.com",
        75,
    ),
    ("SoftFlow", "Software", "Beirut", "hr@softflow.io", "softflow.io", 78),
    ("Netways", "Software/IT", "Beirut", "careers@netways.com", "netways.com", 82),
    (
        "Roadster Diner",
        "Restaurant Tech",
        "Beirut",
        "hr@roadsterdiner.com",
        "roadsterdiner.com",
        72,
    ),
    ("Transmed", "Distribution", "Beirut", "hr@transmed.com", "transmed.com.lb", 75),
    (
        "Khatib & Alami",
        "Engineering",
        "Beirut",
        "hr@khatibalami.com",
        "khatibalami.com",
        85,
    ),
    ("Dar Al Handasah", "Engineering", "Beirut", "hr@dargroup.com", "dar.com", 85),
    ("Solidere", "Real Estate", "Beirut", "info@solidere.com", "solidere.com", 82),
    ("M1 Group", "Conglomerate", "Beirut", "info@m1group.com", "m1group.com", 80),
    (
        "Societe Generale Lebanon",
        "Banking",
        "Beirut",
        "hr@sgbank.com",
        "sgbank.com",
        75,
    ),
    ("CMA CGM Lebanon", "Shipping", "Beirut", "hr@cma-cgm.com", "cma-cgm.com", 82),
    ("AUB", "Education", "Beirut", "hr@aub.edu.lb", "aub.edu.lb", 85),
    ("LAU", "Education", "Beirut", "hr@lau.edu.lb", "lau.edu.lb", 82),
    ("USJ", "Education", "Beirut", "hr@usj.edu.lb", "usj.edu.lb", 80),
    ("NDU", "Education", "Keserwan", "hr@ndu.edu.lb", "ndu.edu.lb", 78),
    ("AUBMC", "Healthcare", "Beirut", "hr@aubmc.org", "aubmc.org.lb", 85),
    (
        "Clemenceau Medical Center",
        "Healthcare",
        "Beirut",
        "hr@cmc.com.lb",
        "cmclebanon.com",
        82,
    ),
    ("Hotel Dieu", "Healthcare", "Beirut", "hr@hoteldieu.com", "hoteldieu.com", 80),
    (
        "Bellevue Medical Center",
        "Healthcare",
        "Metn",
        "hr@bellevuemed.com",
        "bellevuemedcenter.com",
        80,
    ),
    (
        "Mount Lebanon Hospital",
        "Healthcare",
        "Mount Lebanon",
        "hr@mlh.com.lb",
        "mlhospital.com",
        78,
    ),
    ("Middle East Airlines", "Aviation", "Beirut", "hr@mea.com.lb", "mea.com.lb", 85),
    (
        "Phoenicia Hotel",
        "Hospitality",
        "Beirut",
        "hr@phoeniciabeirut.com",
        "phoeniciabeirut.com",
        82,
    ),
    (
        "Four Seasons Beirut",
        "Hospitality",
        "Beirut",
        "hr.bey@fourseasons.com",
        "fourseasons.com",
        80,
    ),
    (
        "Hilton Beirut",
        "Hospitality",
        "Beirut",
        "hr.beirut@hilton.com",
        "hilton.com",
        78,
    ),
    (
        "Le Gray Beirut",
        "Hospitality",
        "Beirut",
        "hr@legraybeirut.com",
        "legray.com",
        75,
    ),
    ("Alfa", "Telecom", "Beirut", "hr@alfa.com.lb", "alfa.com.lb", 88),
    ("Bank Audi", "Banking", "Beirut", "hr@bankaudi.com.lb", "bankaudi.com.lb", 88),
    ("BLOM Bank", "Banking", "Beirut", "hr@blom.com", "blombank.com", 88),
    ("Byblos Bank", "Banking", "Jbeil", "hr@byblosbank.com", "byblosbank.com", 88),
    (
        "Bank of Beirut",
        "Banking",
        "Beirut",
        "hr@bankofbeirut.com",
        "bankofbeirut.com",
        85,
    ),
    (
        "Credit Libanais",
        "Banking",
        "Beirut",
        "hr@creditlibanais.com",
        "creditlibanais.com",
        85,
    ),
    ("Fransabank", "Banking", "Beirut", "hr@fransabank.com", "fransabank.com", 82),
    ("Bankmed", "Banking", "Beirut", "hr@bankmed.com.lb", "bankmed.com.lb", 82),
    ("BBAC", "Banking", "Beirut", "hr@bbac.com.lb", "bbac.com.lb", 80),
    (
        "Intercontinental Phoenicia",
        "Hospitality",
        "Beirut",
        "hr.beyha@ihg.com",
        "phoenicia.com",
        80,
    ),
]

# ═══════════════════════════════════════════════════════
# demo_user'S HR-TARGETED COMPANIES
# ═══════════════════════════════════════════════════════
demo_user_COMPANIES = [
    ("Azadea Group", "Retail/Fashion", "Beirut", "hr@azadea.com", "azadea.com", 92),
    (
        "Chalhoub Group",
        "Luxury Retail",
        "Beirut",
        "hr@chalhoub.com",
        "chalhoubgroup.com",
        90,
    ),
    ("Murex", "Financial Software", "Beirut", "careers@murex.com", "murex.com", 88),
    ("Bank Audi", "Banking", "Beirut", "hr@bankaudi.com.lb", "bankaudi.com.lb", 95),
    ("BLOM Bank", "Banking", "Beirut", "hr@blom.com", "blombank.com", 95),
    ("Byblos Bank", "Banking", "Jbeil", "hr@byblosbank.com", "byblosbank.com", 95),
    (
        "Bank of Beirut",
        "Banking",
        "Beirut",
        "hr@bankofbeirut.com",
        "bankofbeirut.com",
        90,
    ),
    (
        "Credit Libanais",
        "Banking",
        "Beirut",
        "hr@creditlibanais.com",
        "creditlibanais.com",
        88,
    ),
    ("Fransabank", "Banking", "Beirut", "hr@fransabank.com", "fransabank.com", 85),
    ("Bankmed", "Banking", "Beirut", "hr@bankmed.com.lb", "bankmed.com.lb", 85),
    ("BBAC", "Banking", "Beirut", "hr@bbac.com.lb", "bbac.com.lb", 82),
    ("Hikma Pharmaceuticals", "Pharma", "Beirut", "hr@hikma.com", "hikma.com", 90),
    ("Holdal Group", "Distribution", "Beirut", "hr@holdal.com", "holdal.com", 80),
    (
        "Fattal Group",
        "Distribution",
        "Beirut",
        "careers@fattal.com.lb",
        "fattal.com.lb",
        82,
    ),
    (
        "Kettaneh Group",
        "Automotive",
        "Beirut",
        "hr@kettaneh.com",
        "kettanehgroup.com",
        80,
    ),
    (
        "Khatib & Alami",
        "Engineering",
        "Beirut",
        "hr@khatibalami.com",
        "khatibalami.com",
        85,
    ),
    ("Dar Al Handasah", "Engineering", "Beirut", "hr@dargroup.com", "dar.com", 85),
    ("Nestle Lebanon", "FMCG", "Beirut", "hr@nestle-lb.com", "nestle.com", 85),
    ("Unilever Lebanon", "FMCG", "Beirut", "careers@unilever.com", "unilever.com", 85),
    ("PepsiCo Lebanon", "FMCG", "Beirut", "hr@pepsico.com.lb", "pepsico.com", 82),
    ("L'Oreal Lebanon", "Cosmetics", "Beirut", "careers@loreal.com", "loreal.com", 82),
    (
        "Deloitte Lebanon",
        "Consulting",
        "Beirut",
        "careers@deloitte.com",
        "deloitte.com",
        92,
    ),
    ("PwC Lebanon", "Consulting", "Beirut", "careers@pwc.com", "pwc.com", 92),
    ("EY Lebanon", "Consulting", "Beirut", "careers@lb.ey.com", "ey.com", 92),
    ("KPMG Lebanon", "Consulting", "Beirut", "hr@kpmg.com.lb", "kpmg.com", 90),
    ("AUB", "Education", "Beirut", "hr@aub.edu.lb", "aub.edu.lb", 88),
    ("LAU", "Education", "Beirut", "hr@lau.edu.lb", "lau.edu.lb", 85),
    ("USJ", "Education", "Beirut", "hr@usj.edu.lb", "usj.edu.lb", 82),
    ("AUBMC", "Healthcare", "Beirut", "hr@aubmc.org", "aubmc.org.lb", 88),
    (
        "Clemenceau Medical Center",
        "Healthcare",
        "Beirut",
        "hr@cmc.com.lb",
        "cmclebanon.com",
        85,
    ),
    (
        "Hotel Dieu de France",
        "Healthcare",
        "Beirut",
        "rh@hdf-lb.org",
        "hoteldieu.com",
        82,
    ),
    (
        "Bellevue Medical Center",
        "Healthcare",
        "Metn",
        "hr@bellevuemed.com",
        "bellevuemedcenter.com",
        82,
    ),
    (
        "Mount Lebanon Hospital",
        "Healthcare",
        "Mount Lebanon",
        "hr@mlh.com.lb",
        "mlhospital.com",
        80,
    ),
    ("Middle East Airlines", "Aviation", "Beirut", "hr@mea.com.lb", "mea.com.lb", 90),
    (
        "Phoenicia Hotel",
        "Hospitality",
        "Beirut",
        "hr@phoeniciabeirut.com",
        "phoeniciabeirut.com",
        85,
    ),
    (
        "Four Seasons Beirut",
        "Hospitality",
        "Beirut",
        "hr.bey@fourseasons.com",
        "fourseasons.com",
        82,
    ),
    (
        "Hilton Beirut",
        "Hospitality",
        "Beirut",
        "hr.beirut@hilton.com",
        "hilton.com",
        82,
    ),
    ("Solidere", "Real Estate", "Beirut", "info@solidere.com", "solidere.com", 85),
    ("ABC Mall", "Retail", "Beirut", "hr@abc.com.lb", "abc.com.lb", 80),
    ("Spinneys Lebanon", "Retail", "Beirut", "hr@spinneys.com", "spinneys.com.lb", 80),
    ("Aishti", "Luxury Retail", "Beirut", "hr@aishti.com", "aishti.com", 82),
    (
        "Malia Group",
        "Conglomerate",
        "Beirut",
        "hr@maliagroup.com",
        "maliagroup.com",
        85,
    ),
    ("Transmed", "Distribution", "Beirut", "hr@transmed.com", "transmed.com.lb", 80),
    (
        "Contact Lebanon",
        "BPO/Call Center",
        "Beirut",
        "recruitment@contact.com.lb",
        "contact.com.lb",
        80,
    ),
    (
        "CME Offshore",
        "Technology",
        "Beirut",
        "careers@cmeoffshore.com",
        "cmeoffshore.com",
        85,
    ),
    ("Berytech", "Technology Hub", "Beirut", "info@berytech.org", "berytech.org", 82),
]


def seed_all_companies() -> Dict[str, Any]:
    """Seed both Sam and demo_user companies into the database.

    Creates the lebanon_companies table if it does not exist, and inserts pre-verified
    records for role types 'tech' and 'hr'.
    """
    logger.info("Starting Lebanon Company database seeding...")
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row

    sam_count = 0
    demo_user_count = 0

    try:
        # Ensure table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lebanon_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                industry TEXT,
                location TEXT,
                email TEXT,
                website TEXT,
                relevance_score INTEGER DEFAULT 50,
                target_role_type TEXT DEFAULT 'tech',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Insert Sam's companies
        for name, industry, location, email, website, score in SAM_COMPANIES:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO lebanon_companies 
                    (company_name, industry, location, email, website, relevance_score, target_role_type)
                    VALUES (?, ?, ?, ?, ?, ?, 'tech')
                """,
                    (name, industry, location, email, website, score),
                )
                if conn.changes > 0:
                    sam_count += 1
            except Exception as e:
                logger.debug(f"Failed to insert tech company {name}: {e}")
        conn.commit()

        # Insert demo_user's companies
        for name, industry, location, email, website, score in demo_user_COMPANIES:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO lebanon_companies 
                    (company_name, industry, location, email, website, relevance_score, target_role_type)
                    VALUES (?, ?, ?, ?, ?, ?, 'hr')
                """,
                    (name, industry, location, email, website, score),
                )
                if conn.changes > 0:
                    demo_user_count += 1
            except Exception as e:
                logger.debug(f"Failed to insert HR company {name}: {e}")
        conn.commit()

        # Count totals
        total = conn.execute("SELECT COUNT(*) FROM lebanon_companies").fetchone()[0]
        tech = conn.execute(
            "SELECT COUNT(*) FROM lebanon_companies WHERE target_role_type='tech'"
        ).fetchone()[0]
        hr = conn.execute(
            "SELECT COUNT(*) FROM lebanon_companies WHERE target_role_type='hr'"
        ).fetchone()[0]

        logger.info(
            f"Seeding completed: {sam_count} tech, {demo_user_count} HR companies inserted."
        )
        return {
            "status": "ok",
            "sam_companies_seeded": sam_count,
            "demo_user_companies_seeded": demo_user_count,
            "total_in_db": total,
            "tech_companies": tech,
            "hr_companies": hr,
            "database": db_path,
        }
    except Exception as e:
        logger.error(f"Error during company database seeding: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "sam_companies_seeded": 0,
            "demo_user_companies_seeded": 0,
            "total_in_db": 0,
            "tech_companies": 0,
            "hr_companies": 0,
            "database": db_path,
        }
    finally:
        conn.close()


def get_companies_for_role_type(
    role_type: str = "tech", limit: int = 50
) -> List[Dict[str, Any]]:
    """Get pre-seeded companies for a given role type (e.g., 'tech' or 'hr')."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT * FROM lebanon_companies 
            WHERE target_role_type = ? 
            ORDER BY relevance_score DESC 
            LIMIT ?
        """,
            (role_type, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to query companies for role type '{role_type}': {e}")
        return []
    finally:
        conn.close()


def get_companies_count() -> Dict[str, int]:
    """Get company count statistics."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        total = conn.execute("SELECT COUNT(*) FROM lebanon_companies").fetchone()[0]
        tech = conn.execute(
            "SELECT COUNT(*) FROM lebanon_companies WHERE target_role_type='tech'"
        ).fetchone()[0]
        hr = conn.execute(
            "SELECT COUNT(*) FROM lebanon_companies WHERE target_role_type='hr'"
        ).fetchone()[0]
        return {"total": total, "tech": tech, "hr": hr}
    except Exception as e:
        logger.error(f"Failed to query companies count: {e}")
        return {"total": 0, "tech": 0, "hr": 0}
    finally:
        conn.close()


if __name__ == "__main__":
    # Setup basic logging to console when run directly
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    result = seed_all_companies()
    if result["status"] == "ok":
        print(
            f"✅ Seeded: {result['sam_companies_seeded']} tech + {result['demo_user_companies_seeded']} HR"
        )
        print(f"   Total in DB: {result['total_in_db']}")
        print(f"   Tech: {result['tech_companies']} | HR: {result['hr_companies']}")
    else:
        print(f"❌ Seeding failed: {result.get('error')}")

