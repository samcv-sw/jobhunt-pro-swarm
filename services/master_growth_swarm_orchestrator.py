"""
services/master_growth_swarm_orchestrator.py - 24/7 Unified Autonomous Cloud Growth & Outreach Swarm Orchestrator
Connects scrapers, intent enrichment, vector ATS matching, deliverability verification, and Telegram alerts into a single 24/7 $0 Cloud Swarm.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from services.company_email_pattern_engine import company_email_pattern_engine
from services.email_spam_scanner_service import email_spam_scanner_service
from services.lead_enrichment_engine import LeadEnrichmentEngine
from services.edge_vector_matcher_v3 import edge_vector_matcher_v3
from services.sdr_alert_dispatcher import SDRAlertDispatcher

logger = logging.getLogger(__name__)


class MasterGrowthSwarmOrchestrator:
    """
    Unified 24/7 Autonomous Lead & SDR Swarm Controller.
    Runs with 0$ cloud overhead on background crons or REST triggers.
    """

    def __init__(self):
        self.alert_dispatcher = SDRAlertDispatcher()

    def process_lead_end_to_end(
        self,
        lead_data: Dict[str, Any],
        candidate_profile: Optional[Dict[str, Any]] = None,
        dispatch_alerts: bool = True
    ) -> Dict[str, Any]:
        """
        Executes complete pipeline:
        1. Calculate intent score & extract signals
        2. Verify or infer contact email pattern
        3. Match candidate skills via vector engine
        4. Validate email copy with spam scanner
        5. Trigger Telegram alert if high intent
        """
        start_time = time.perf_counter()

        company = lead_data.get("company", "Target Company")
        title = lead_data.get("title", "Target Role")
        email = lead_data.get("contact_email") or lead_data.get("email") or ""
        domain = lead_data.get("domain") or company_email_pattern_engine.clean_domain(company.replace(" ", "") + ".com")

        # Step 1: Intent Score & Hook Generation
        intent_score = LeadEnrichmentEngine.calculate_intent_score(lead_data)
        hook_info = LeadEnrichmentEngine.generate_personalized_hook(
            lead_data,
            candidate_name=candidate_profile.get("full_name", "Candidate") if candidate_profile else "Candidate"
        )

        # Step 2: Email Discovery / Pattern Verification
        email_intelligence = {}
        if not email and domain:
            email_intelligence = company_email_pattern_engine.generate_candidate_emails(
                first_name="Hiring",
                last_name="Manager",
                company_domain=domain,
                verify_mx=True
            )
            email = email_intelligence.get("primary_candidate") or f"careers@{domain}"

        # Step 3: Vector Resume / Job Match
        candidate_skills = candidate_profile.get("skills", ["python", "fastapi", "ai", "cloud"]) if candidate_profile else ["general"]
        vector_match = edge_vector_matcher_v3.match_resume_vector(candidate_skills, top_k=3)

        # Step 4: Spam Scanner Check on generated copy
        spam_scan = email_spam_scanner_service.scan_content(
            subject=hook_info.get("subject", ""),
            body=hook_info.get("hook_opening", "")
        )

        # Step 5: Telegram Push Alert for High-Value Leads (Intent >= 70)
        alert_sent = False
        if dispatch_alerts and intent_score >= 70:
            msg = (
                f"🚀 <b>24/7 AUTONOMOUS SWARM: HIGH INTENT LEAD DETECTED!</b>\n\n"
                f"🏢 <b>Company:</b> {company}\n"
                f"💼 <b>Role:</b> {title}\n"
                f"🎯 <b>Intent Score:</b> {intent_score}%\n"
                f"✉️ <b>Target Email:</b> {email}\n"
                f"🛡️ <b>Inbox Placement Score:</b> {spam_scan.get('inbox_placement_score')}%\n\n"
                f"⚡ <b>Status:</b> Ready for Autonomous Dispatch."
            )
            alert_sent = self.alert_dispatcher.send_telegram_alert(msg)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "success": True,
            "latency_ms": latency_ms,
            "company": company,
            "title": title,
            "target_email": email,
            "intent_score": intent_score,
            "hook": hook_info,
            "vector_match": vector_match,
            "spam_analysis": spam_scan,
            "alert_dispatched": alert_sent,
            "cloud_autonomy_ready": True
        }

    def run_swarm_batch(
        self,
        leads: List[Dict[str, Any]],
        candidate_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process batch of scraped leads through the full autonomous pipeline."""
        results = []
        high_intent_count = 0

        for lead in leads:
            res = self.process_lead_end_to_end(lead, candidate_profile=candidate_profile, dispatch_alerts=False)
            results.append(res)
            if res.get("intent_score", 0) >= 70:
                high_intent_count += 1

        return {
            "total_processed": len(leads),
            "high_intent_leads": high_intent_count,
            "leads": results,
            "batch_completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }


master_growth_swarm_orchestrator = MasterGrowthSwarmOrchestrator()
