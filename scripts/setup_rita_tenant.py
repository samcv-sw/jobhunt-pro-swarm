import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import sqlite3
import logging
import uuid
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jobhunt_saas_v2.db')


def create_rita() -> bool:
    """Create Rita Cordahi as a tenant in the SaaS database.

    Returns:
        True on success, False on failure.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        logger.error(f"[setup_rita] Failed to connect to database: {e}")
        return False

    try:
        # ── User ──────────────────────────────────────────────────────────────
        try:
            existing = conn.execute(
                "SELECT * FROM users WHERE email = ?", ("ritacordahi2@gmail.com",)
            ).fetchone()
        except Exception as e:
            logger.error(f"[setup_rita] Failed to query users table: {e}")
            logger.error("[setup_rita] Is the schema initialized? Run web/app.py first.")
            return False

        if existing:
            rita_user_id = existing["user_id"]
            logger.info(f"[OK] Rita already exists: {rita_user_id}")
        else:
            rita_user_id = f"rita_{uuid.uuid4().hex[:12]}"
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            try:
                conn.execute(
                    "INSERT INTO users (user_id, name, email, phone, password_hash, created_at, is_active, user_type) "
                    "VALUES (?, ?, ?, ?, ?, ?, 1, 'jobseeker')",
                    (rita_user_id, "Rita Cordahi", "ritacordahi2@gmail.com",
                     "+961 76 005 412", "ritatenant_api_nopass", now)
                )
                conn.commit()
                logger.info(f"[OK] Created Rita user: {rita_user_id}")
            except Exception as e:
                logger.error(f"[setup_rita] Failed to create Rita user: {e}")
                conn.rollback()
                return False

        # ── CV Profile ────────────────────────────────────────────────────────
        try:
            existing_p = conn.execute(
                "SELECT * FROM cv_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (rita_user_id,)
            ).fetchone()
        except Exception as e:
            logger.warning(f"[setup_rita] Could not check cv_profiles: {e}")
            existing_p = None

        if existing_p:
            profile_id = existing_p["id"]
            logger.info(f"[OK] Rita CV profile exists: {profile_id}")
        else:
            rita_cv = """RITA CORDAHI
ritacordahi2@gmail.com | +961 76 005 412 | Beirut, Lebanon
linkedin.com/in/rita-cordahi/

PROFESSIONAL SUMMARY
HR & Customer Operations Specialist with 5+ years of experience in human resources, recruitment coordination, customer service operations, and administrative management. Proven track record in employee onboarding, HRIS management, payroll coordination, and performance management systems.

PROFESSIONAL EXPERIENCE
HR & Operations Coordinator | Rita Consulting | 2020 - Present
- Manage end-to-end recruitment cycles for 50+ positions annually
- Coordinate employee onboarding, training, and development programs
- Maintain HRIS database with 100% data accuracy
- Process payroll for 200+ employees monthly
- Implement performance management system improving review completion by 40%
- Handle employee relations cases with 95% resolution rate

Administrative Manager | ABC Corp | 2018 - 2020
- Managed office operations for 150+ employee organization

EDUCATION
Bachelor's Degree in Business Administration - Lebanese University

SKILLS
HR Operations, Recruitment, Employee Onboarding, HRIS, Payroll Coordination, Performance Management, Employee Relations, Customer Service Operations, Process Improvement, Policy Development, Data Entry, Microsoft Office Suite, Communication, Problem Solving

LANGUAGES
Arabic (Native), English (Fluent), French (Intermediate)
"""
            try:
                conn.execute(
                    "INSERT INTO cv_profiles (user_id, cv_text, skills, experience_years, target_titles, "
                    "target_locations, created_at, profile_name, min_local_salary) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (rita_user_id, rita_cv,
                     "HR operations, customer service, recruitment, onboarding, employee relations, HRIS, payroll coordination, performance management, training & development",
                     5,
                     "HR Operations Manager, HR Coordinator, Customer Operations Specialist, Recruitment Specialist, People Operations Manager, HR Generalist, Talent Acquisition Coordinator",
                     "Lebanon (Beirut, Jbeil, Keserwan, Metn, Mount Lebanon)",
                     time.strftime('%Y-%m-%d %H:%M:%S'),
                     "Rita Cordahi - HR Professional",
                     1500)
                )
                conn.commit()
                profile_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                logger.info(f"[OK] Created Rita CV profile: {profile_id}")
            except Exception as e:
                logger.error(f"[setup_rita] Failed to create Rita CV profile: {e}")
                conn.rollback()
                profile_id = 0

        # ── Campaign ─────────────────────────────────────────────────────────
        try:
            existing_c = conn.execute(
                "SELECT * FROM campaigns WHERE user_id = ? AND status IN ('pending','running','paused') "
                "ORDER BY id DESC LIMIT 1",
                (rita_user_id,)
            ).fetchone()
        except Exception as e:
            logger.warning(f"[setup_rita] Could not check campaigns: {e}")
            existing_c = None

        if existing_c:
            campaign_id = existing_c["campaign_id"]
            logger.info(f"[OK] Rita campaign exists: {campaign_id}")
        else:
            campaign_id = f"rita_camp_{uuid.uuid4().hex[:8]}"
            rita_companies_count = 50
            try:
                conn.execute(
                    "INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, status, "
                    "total_companies, sent_count, created_at, bouquets) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                    (campaign_id, rita_user_id, 'rita_setup_free', profile_id, "pending",
                     rita_companies_count, time.strftime('%Y-%m-%d %H:%M:%S'), "Priority Shield,Stealth Mode")
                )
                conn.commit()
                logger.info(f"[OK] Created Rita campaign: {campaign_id}")
            except Exception as e:
                logger.error(f"[setup_rita] Failed to create Rita campaign: {e}")
                conn.rollback()

        # ── Verify ────────────────────────────────────────────────────────────
        try:
            users = conn.execute("SELECT user_id, name, email FROM users WHERE is_active=1").fetchall()
            logger.info(f"\n=== Active Users: {len(users)} ===")
            for u in users:
                camps = conn.execute(
                    "SELECT COUNT(*) as cnt FROM campaigns WHERE user_id=?", (u["user_id"],)
                ).fetchone()
                logger.info(f"  {u['name']} ({u['email']}) - {camps['cnt']} campaigns")
        except Exception as e:
            logger.warning(f"[setup_rita] Could not run verification query: {e}")

        logger.info("\n[DONE] Rita Cordahi tenant setup complete!")
        return True

    except Exception as e:
        logger.error(f"[setup_rita] Unexpected error during setup: {e}", exc_info=True)
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    success = create_rita()
    sys.exit(0 if success else 1)
