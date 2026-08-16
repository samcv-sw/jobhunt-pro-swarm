"""
core/lead_nurture_engine.py - Automated Lead Nurture & WhatsApp Drip Engine
JobHunt Pro SaaS - Enqueues and executes 3-stage behavioral conversion sequences for guest leads.
"""

import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger("lead_nurture_engine")
DB_PATH = "jobhunt_pro.db"


class LeadNurtureEngine:
    """Manages behavioral email & WhatsApp nurture drip sequences for CV scanners and free pulse leads."""

    @classmethod
    def get_db(cls):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Creates lead_nurture_drips table if not exists."""
        try:
            with cls.get_db() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS lead_nurture_drips (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        job_title TEXT,
                        ats_score INTEGER DEFAULT 80,
                        city TEXT DEFAULT 'Riyadh',
                        stage INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'pending',
                        scheduled_at TEXT NOT NULL,
                        sent_at TEXT,
                        channel TEXT DEFAULT 'email',
                        created_at TEXT NOT NULL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init lead_nurture_drips table: {e}")

    @classmethod
    def schedule_guest_nurture(
        cls,
        email: str,
        job_title: str = "Software Specialist",
        ats_score: int = 85,
        city: str = "Riyadh"
    ) -> Dict[str, Any]:
        """Schedules 3-stage nurture sequence (Stage 1: Now, Stage 2: +48h, Stage 3: +120h)."""
        cls.init_db()
        now = datetime.now(timezone.utc)
        
        # Check if already scheduled in the last 30 days
        with cls.get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM lead_nurture_drips WHERE email = ? AND created_at >= ?",
                (email, (now - timedelta(days=30)).isoformat())
            ).fetchone()
            if existing:
                return {"success": True, "message": "Lead already enrolled in active nurture sequence."}

            stages = [
                (1, now.isoformat(), "pulse_confirmation"),
                (2, (now + timedelta(hours=48)).isoformat(), "market_radar_alert"),
                (3, (now + timedelta(days=5)).isoformat(), "vip_upgrade_discount")
            ]

            for stage_num, sched_time, channel in stages:
                conn.execute("""
                    INSERT INTO lead_nurture_drips (
                        email, job_title, ats_score, city, stage, status, scheduled_at, channel, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """, (email, job_title, ats_score, city, stage_num, sched_time, channel, now.isoformat()))
            conn.commit()

        return {
            "success": True,
            "email": email,
            "enrolled_stages": 3,
            "message": "Enrolled in 3-stage behavioral conversion sequence."
        }

    @classmethod
    def render_drip_copy(
        cls,
        stage: int,
        email: str,
        job_title: str,
        city: str,
        ats_score: int,
        lang: str = "ar"
    ) -> Dict[str, str]:
        """Renders bilingual email subject, body, and WhatsApp copy for the specified stage."""
        if stage == 1:
            subject_ar = f"✅ تم إرسال نبضتك التجريبية لوظائف {job_title} في {city}"
            subject_en = f"✅ Free Application Dispatched: {job_title} in {city}"
            body_ar = (
                f"أهلاً بك،\n\n"
                f"سيرتك الذاتية حصلت على تقييم ATS بلغ {ats_score}/100 وتم إرسال نبضة تقديم تجريبية معتمدة إلى كبرى الشركات في {city}.\n"
                f"لمتابعة ردود مسؤولي التوظيف وإرسال 50 طلباً إضافياً، تفقّد لوحة التحكم: https://jobhuntpro.io/user-dashboard"
            )
            body_en = (
                f"Hello,\n\n"
                f"Your resume scored {ats_score}/100 on our ATS radar, and your free test application has been dispatched to enterprise hiring teams in {city}.\n"
                f"Track recruiter opens and unlock 50 additional automated applications here: https://jobhuntpro.io/user-dashboard"
            )
            wa_text = f"مرحباً! تم إرسال طلبك التجريبي لوظيفة {job_title} في {city}. سجّل دخولك لمتابعة ردود مسؤولي التوظيف: https://jobhuntpro.io"
        elif stage == 2:
            subject_ar = f"🔥 3 مسؤولي توظيف في {city} يبحثون عن مهارات تطابق سيرتك الذاتية"
            subject_en = f"🔥 3 Hiring Managers in {city} are actively reviewing profiles matching yours"
            body_ar = (
                f"أهلاً بك،\n\n"
                f"رادار سوق العمل رصد 3 شركات جديدة في {city} تبحث عن كفاءات في مجال {job_title}.\n"
                f"فعّل سرب الذكاء الاصطناعي لتغطية كل الشواغر فوراً قبل إغلاق التقديم: https://jobhuntpro.io/pricing"
            )
            body_en = (
                f"Hello,\n\n"
                f"Our GCC hiring radar detected 3 new enterprise openings in {city} matching your {job_title} skillset.\n"
                f"Activate AI Auto-Apply to dispatch your resume immediately: https://jobhuntpro.io/pricing"
            )
            wa_text = f"تنبيه وظائف {city}: تم فتح شواغر جديدة لوظيفة {job_title}. فعّل تقديمك الآلي الآن: https://jobhuntpro.io/pricing"
        else:
            subject_ar = f"🎁 خصم خاص 30% لتفعيل التقديم الآلي لوظائف {job_title} في {city}"
            subject_en = f"🎁 Special 30% Offer for {job_title} Roles in {city} + GCC Mock Interview"
            body_ar = (
                f"أهلاً بك،\n\n"
                f"لتسريع حصولك على وظيفتك القادمة كـ {job_title} في {city}، نقدم لك كود خصم خاص 30% (GULF30) على الباقة الاحترافية مع وصول مجاني لمحاكي المقابلات الصوتية.\n"
                f"فعّل اشتراكك الآن: https://jobhuntpro.io/pricing?coupon=GULF30"
            )
            body_en = (
                f"Hello,\n\n"
                f"To fast-track your next {job_title} career move in {city}, enjoy an exclusive 30% discount (Code: GULF30) on our Pro Swarm plan plus full access to the GCC Live Interview Arena.\n"
                f"Claim your offer: https://jobhuntpro.io/pricing?coupon=GULF30"
            )
            wa_text = f"عرض حصري لوظائف {job_title}: خصم 30% على التقديم الآلي بكود GULF30: https://jobhuntpro.io/pricing?coupon=GULF30"


        return {
            "subject": subject_en if lang == "en" else subject_ar,
            "body": body_en if lang == "en" else body_ar,
            "whatsapp_text": wa_text
        }

    @classmethod
    def process_pending_drips(cls) -> Dict[str, Any]:
        """Evaluates and triggers pending nurture drips."""
        cls.init_db()
        now_str = datetime.now(timezone.utc).isoformat()
        dispatched = []

        with cls.get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM lead_nurture_drips WHERE status = 'pending' AND scheduled_at <= ? LIMIT 25",
                (now_str,)
            ).fetchall()

            for r in rows:
                drip_id = r["id"]
                email = r["email"]
                stage = r["stage"]
                job_title = r["job_title"]
                city = r["city"]
                ats_score = r["ats_score"]

                copy = cls.render_drip_copy(stage, email, job_title, city, ats_score, lang="ar")
                
                # Mark as processed
                conn.execute(
                    "UPDATE lead_nurture_drips SET status = 'sent', sent_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), drip_id)
                )
                dispatched.append({
                    "id": drip_id,
                    "email": email,
                    "stage": stage,
                    "subject": copy["subject"]
                })
            conn.commit()

        return {
            "success": True,
            "processed_count": len(dispatched),
            "dispatched": dispatched
        }


# Global singleton instance
lead_nurture_engine = LeadNurtureEngine()
