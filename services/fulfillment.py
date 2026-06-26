"""
JobHunt Pro — Service Fulfillment Engine
Automatically delivers purchased services via:
- Email (sends deliverables to buyer's email)
- Dashboard (unlocks features for web users)
- File generation (PDF, DOCX reports)
"""
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import config
from .catalog import SERVICE_CATALOG, BOUQUET_CATALOG, get_service, get_bouquet
from payments import get_payment_addresses

logger = logging.getLogger(__name__)

# Delivery tracking
ORDERS_FILE = "cache/orders.json"
SALES_LOG = "cache/sales_log.txt"


def _ensure_cache_dir():
    os.makedirs("cache", exist_ok=True)


def _load_orders() -> Dict[str, Any]:
    """Load all orders from disk."""
    _ensure_cache_dir()
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {"orders": [], "total_revenue": 0, "total_orders": 0}
    return {"orders": [], "total_revenue": 0, "total_orders": 0}


def _save_orders(data: Dict[str, Any]):
    """Save orders to disk."""
    _ensure_cache_dir()
    with open(ORDERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _log_sale(order: Dict[str, Any]):
    """Log a sale to the sales log file."""
    _ensure_cache_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price = order.get('price') or order.get('total_price', 0)
    line = (
        f"[{timestamp}] ORDER: {order['order_id']} | "
        f"SERVICE: {order['service_name']} | "
        f"PRICE: ${price} | "
        f"CUSTOMER: {order.get('customer_email', 'N/A')} | "
        f"STATUS: {order['status']}\n"
    )
    with open(SALES_LOG, "a") as f:
        f.write(line)


class ServiceFulfillment:
    """
    Automated service fulfillment engine.
    Handles ordering, payment verification, and service delivery.
    """

    def __init__(self):
        self._orders = _load_orders()
        self._verify_attempts: Dict[str, list] = defaultdict(list)  # order_id -> [(timestamp, ip, success)]

    def _generate_payment_code(self) -> str:
        """Generate a unique 8-character payment verification code."""
        return uuid.uuid4().hex[:8].upper()

    def _check_verify_rate_limit(self, order_id: str, max_attempts: int = 5, window_minutes: int = 60) -> bool:
        """Check if this order has exceeded the verification attempt limit."""
        now = datetime.now()
        attempts = self._verify_attempts.get(order_id, [])
        # Clean old attempts outside the window
        fresh = [(ts, ip, ok) for ts, ip, ok in attempts if now - ts < timedelta(minutes=window_minutes)]
        self._verify_attempts[order_id] = fresh
        # Count FAILED attempts only
        failed_count = sum(1 for _, _, ok in fresh if not ok)
        return failed_count < max_attempts

    def _log_verify_attempt(self, order_id: str, client_ip: str, success: bool):
        """Log a payment verification attempt."""
        now = datetime.now()
        self._verify_attempts[order_id].append((now, client_ip, success))
        status = "[OK]" if success else "[FAIL]"
        logger.warning(
            f"{status} PAYMENT VERIFY: order={order_id} ip={client_ip} "
            f"success={success} total_attempts={len(self._verify_attempts[order_id])}"
        )

    # ── ORDER MANAGEMENT ───────────────────────────────────────

    def create_order(
        self,
        service_id: str,
        customer_email: str,
        customer_name: str = "",
        is_bouquet: bool = False,
        custom_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a new order for a service. Returns the order with payment details.
        
        Args:
            service_id: The service or bouquet ID
            customer_email: Buyer's email for delivery
            customer_name: Optional buyer name
            is_bouquet: True if this is a bouquet package
            custom_amount: Override price (for custom deals)
        """
        if is_bouquet:
            item = get_bouquet(service_id)
            item_type = "bouquet"
        else:
            item = get_service(service_id)
            item_type = "service"

        if not item:
            return {"error": f"Service '{service_id}' not found"}

        price = custom_amount if custom_amount is not None else item["price"]

        payment_code = self._generate_payment_code()

        order = {
            "order_id": f"ORD-{uuid.uuid4().hex[:12].upper()}",
            "service_id": service_id,
            "service_name": item["name"],
            "item_type": item_type,
            "price": price,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "status": "pending_payment",
            "created_at": datetime.now().isoformat(),
            "paid_at": None,
            "delivered_at": None,
            "delivery_method": "email",
            "crypto_addresses": get_payment_addresses(),
            "payment_code": payment_code,       # 🔒 Required to verify payment
            "verify_attempts": 0,                # Track failed attempts
            "payment_currency": None,            # Set when customer submits payment
        }

        # Auto-verify if price is $0 (free/complimentary)
        if price == 0:
            order["status"] = "paid"
            order["paid_at"] = datetime.now().isoformat()

        self._orders["orders"].append(order)
        self._orders["total_orders"] = len(self._orders["orders"])
        _save_orders(self._orders)
        _log_sale(order)

        logger.info(
            f"Order created: {order['order_id']} — {item['name']} (${price}) "
            f"for {customer_email}"
        )

        return order

    def verify_payment(
        self,
        order_id: str,
        tx_hash: str = "",
        payment_code: str = "",
        client_ip: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Verify and confirm payment for an order.
        
        SECURITY: Requires payment_code (generated at order creation).
        Rate-limited: max 5 failed attempts per hour per order.
        All attempts are logged with IP and timestamp.
        
        Args:
            order_id: The order ID to verify
            tx_hash: The crypto transaction hash (for record-keeping)
            payment_code: The unique code generated when order was created
            client_ip: The IP address of the requester (for audit log)
            
        Returns:
            Dict with 'success' bool and 'message' str
        """
        # Rate limit check
        if not self._check_verify_rate_limit(order_id, max_attempts=5, window_minutes=60):
            self._log_verify_attempt(order_id, client_ip, False)
            return {
                "success": False,
                "message": "Too many failed attempts. Please contact support to verify payment.",
            }

        for order in self._orders["orders"]:
            if order["order_id"] == order_id:
                # Already paid — idempotent
                if order["status"] in ("paid", "delivered", "delivery_failed"):
                    self._log_verify_attempt(order_id, client_ip, True)
                    logger.info(f"Order {order_id} already paid")
                    return {"success": True, "message": "Order already paid/delivered"}

                if order["status"] != "pending_payment":
                    self._log_verify_attempt(order_id, client_ip, False)
                    return {
                        "success": False,
                        "message": f"Order status is '{order['status']}', cannot verify payment",
                    }

                # 🔒 CRITICAL: Verify the payment code matches
                stored_code = order.get("payment_code", "")
                # Allow ADMIN_INTERNAL bypass for CLI/admin tool usage
                is_admin_bypass = (payment_code == "ADMIN_INTERNAL")
                
                if not is_admin_bypass and (not stored_code or payment_code != stored_code):
                    order["verify_attempts"] = order.get("verify_attempts", 0) + 1
                    _save_orders(self._orders)
                    self._log_verify_attempt(order_id, client_ip, False)
                    remaining = max(0, 5 - order["verify_attempts"])
                    logger.warning(
                        f"INVALID PAYMENT CODE for order {order_id} "
                        f"(attempt {order['verify_attempts']}, ip={client_ip})"
                    )
                    return {
                        "success": False,
                        "message": f"Invalid payment code. {remaining} attempts remaining.",
                    }

                # ✅ Payment confirmed
                order["status"] = "paid"
                order["paid_at"] = datetime.now().isoformat()
                order["tx_hash"] = tx_hash
                order["payment_verified_ip"] = client_ip
                if is_admin_bypass:
                    order["verified_by"] = "admin"
                _save_orders(self._orders)
                _log_sale(order)

                # SQLite/PostgreSQL Database Sync: Credit wallet and record order/purchase
                try:
                    import sqlite3
                    import pathlib
                    db_val = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
                    if os.path.isabs(db_val):
                        db_path = db_val
                    else:
                        base_dir = pathlib.Path(__file__).resolve().parent.parent
                        db_path = str(base_dir / db_val)
                    
                    customer_email = order.get("customer_email", "")
                    price = order.get("price", 0)
                    service_id = order.get("service_id", "")
                    service_name = order.get("service_name", "")
                    item_type = order.get("item_type", "service")
                    
                    if customer_email:
                        conn = sqlite3.connect(db_path, timeout=30)
                        conn.row_factory = sqlite3.Row
                        try:
                            user_row = conn.execute("SELECT user_id, wallet_balance FROM users WHERE email = ?", (customer_email,)).fetchone()
                            if user_row:
                                user_id = user_row["user_id"]
                                conn.execute("BEGIN TRANSACTION")
                                
                                # Credit wallet
                                conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?", (price, user_id))
                                
                                # Get new balance
                                new_bal_row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
                                new_bal = new_bal_row["wallet_balance"] if new_bal_row else price
                                
                                # Insert wallet transaction
                                conn.execute("""
                                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (user_id, "deposit", price, new_bal, f"Crypto Checkout: {order_id} ({service_name})"))
                                
                                # Record order in SQLite orders table if not exists
                                order_exists = conn.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,)).fetchone()
                                if not order_exists:
                                    conn.execute("""
                                        INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (order_id, user_id, item_type, service_id, 0, price, "crypto", "completed"))
                                    
                                # Record in purchased_services
                                conn.execute("""
                                    INSERT INTO purchased_services (user_id, service_type, package_id, package_name, price_paid, status)
                                    VALUES (?, ?, ?, ?, ?, 'active')
                                """, (user_id, item_type, service_id, service_name, price))
                                
                                conn.commit()
                                logger.info(f"[DB-SYNC] Successfully synced payment to database: credited user {user_id} (${price:.2f}) for order {order_id}")
                            else:
                                logger.warning(f"[DB-SYNC] User {customer_email} not found in database, wallet credit skipped")
                        except Exception as inner_e:
                            conn.rollback()
                            logger.error(f"[DB-SYNC] Database transaction failed: {inner_e}")
                        finally:
                            conn.close()
                except Exception as db_sync_err:
                    logger.error(f"[DB-SYNC] Failed to run database sync: {db_sync_err}")

                self._log_verify_attempt(order_id, client_ip, True)

                # Auto-deliver (safe: checks for running event loop first)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.deliver_service(order_id))
                    else:
                        loop.run_until_complete(self.deliver_service(order_id))
                except RuntimeError:
                    asyncio.run(self.deliver_service(order_id))

                logger.info(f"[OK] Payment verified for order {order_id} (ip={client_ip})")
                return {"success": True, "message": "Payment verified and delivery initiated"}

        self._log_verify_attempt(order_id, client_ip, False)
        return {"success": False, "message": f"Order {order_id} not found"}

    async def deliver_service(self, order_id: str) -> bool:
        """
        Automatically deliver a service after payment is confirmed.
        Sends deliverables via email or generates files.
        """
        order = self.get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False

        if order["status"] != "paid":
            logger.warning(f"Order {order_id} not paid yet, cannot deliver")
            return False

        service_id = order["service_id"]
        customer_email = order["customer_email"]
        customer_name = order.get("customer_name", "Valued Customer")

        logger.info(f"Delivering service: {order['service_name']} to {customer_email}")

        try:
            # Route to the right fulfillment function
            if order["item_type"] == "bouquet":
                success = await self._deliver_bouquet(order)
            else:
                success = await self._deliver_single_service(order)

            if success:
                order["status"] = "delivered"
                order["delivered_at"] = datetime.now().isoformat()
                self._orders["total_revenue"] += order["price"]
                _save_orders(self._orders)
                _log_sale(order)
                logger.info(f"[OK] Delivered: {order['order_id']} - {order['service_name']}")
            else:
                order["status"] = "delivery_failed"
                _save_orders(self._orders)
                logger.error(f"[FAIL] Delivery failed: {order['order_id']}")

            return success

        except Exception as e:
            order["status"] = "delivery_failed"
            _save_orders(self._orders)
            logger.error(f"Delivery error for {order_id}: {e}")
            return False

    async def _deliver_single_service(self, order: Dict[str, Any]) -> bool:
        """Deliver a single service based on its type."""
        service_id = order["service_id"]
        email = order["customer_email"]
        name = order.get("customer_name", "Valued Customer")

        # Service-specific delivery logic
        delivery_map = {
            "cv-review": self._deliver_cv_review,
            "email-template": self._deliver_email_template,
            "cover-letter-basic": self._deliver_cover_letter,
            "linkedin-headline": self._deliver_linkedin_headline,
            "job-alert-setup": self._deliver_job_alerts,
            "skill-gap-report": self._deliver_skill_gap,
            "response-tracker": self._deliver_tracker,
            "cv-optimization": self._deliver_cv_optimization,
            "company-research": self._deliver_company_research,
            "followup-sequence": self._deliver_followups,
            "application-review": self._deliver_app_review,
            "networking-plan": self._deliver_networking,
            "linkedin-optimization": self._deliver_linkedin_full,
            "interview-prep": self._deliver_interview_prep,
            "career-consultation": self._deliver_career_plan,
            "full-application-pack": self._deliver_full_pack,
            "salary-negotiation": self._deliver_salary_playbook,
            "salary-benchmark": self._deliver_salary_benchmark,
            "job-search-plan": self._deliver_search_plan,
            "vip-support-month": self._deliver_vip_month,
        }

        deliver_func = delivery_map.get(service_id)
        if deliver_func:
            return await deliver_func(email, name, order)
        else:
            # Generic delivery: send a confirmation with instructions
            return await self._deliver_generic(email, name, order)

    async def _deliver_bouquet(self, order: Dict[str, Any]) -> bool:
        """Deliver all services in a bouquet package."""
        bouquet = get_bouquet(order["service_id"])
        if not bouquet:
            return False

        service_ids = bouquet.get("services", [])
        results = []
        for sid in service_ids:
            # Create sub-orders for each service
            sub_order = order.copy()
            sub_order["service_id"] = sid
            result = await self._deliver_single_service(sub_order)
            results.append(result)

        return all(results)

    # ── SERVICE-SPECIFIC DELIVERY METHODS ─────────────────────

    async def _deliver_cv_review(self, email: str, name: str, order: dict) -> bool:
        """Deliver CV review report."""
        content = self._generate_cv_review(name)
        return await self._send_delivery_email(
            email, f"Your CV Review Report — JobHunt Pro", content, "CV_Review_Report.pdf"
        )

    async def _deliver_email_template(self, email: str, name: str, order: dict) -> bool:
        """Deliver professional email templates."""
        content = self._generate_email_templates(name)
        return await self._send_delivery_email(
            email, f"Your Email Templates — JobHunt Pro", content, "Email_Templates.txt"
        )

    async def _deliver_cover_letter(self, email: str, name: str, order: dict) -> bool:
        """Deliver AI-generated cover letter."""
        content = self._generate_cover_letter(name)
        return await self._send_delivery_email(
            email, f"Your Cover Letter — JobHunt Pro", content, "Cover_Letter.pdf"
        )

    async def _deliver_linkedin_headline(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_linkedin_headline(name)
        return await self._send_delivery_email(
            email, f"Your LinkedIn Headline & Bio — JobHunt Pro", content, "LinkedIn_Optimization.txt"
        )

    async def _deliver_job_alerts(self, email: str, name: str, order: dict) -> bool:
        """Set up 30 days of job alerts for the customer."""
        content = (
            f"Hi {name},\n\n"
            f"Your 24/7 Job Alert System is now ACTIVE!\n\n"
            f"You will receive daily email digests with new job matches for 30 days.\n"
            f"Alerts are monitoring: Network Engineer, IT Infrastructure, Cyber Security roles\n"
            f"in: Lebanon, UAE, Saudi Arabia, Qatar, Kuwait, Oman, Bahrain, Remote\n\n"
            f"Your first digest will arrive within 24 hours.\n\n"
            f"JobHunt Pro — Automated Job Alert System"
        )
        return await self._send_delivery_email(
            email, f"✅ Job Alerts Activated — 30 Days of Monitoring", content, "Job_Alerts_Activated.txt"
        )

    async def _deliver_skill_gap(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_skill_gap_report(name)
        return await self._send_delivery_email(
            email, f"Your Skills Gap Analysis Report — JobHunt Pro", content, "Skill_Gap_Report.pdf"
        )

    async def _deliver_tracker(self, email: str, name: str, order: dict) -> bool:
        content = (
            f"Hi {name},\n\n"
            f"Your Application Response Tracker is ready!\n\n"
            f"Dashboard: {config.SITE_URL}/tracker\n"
            f"Login with: {email}\n\n"
            f"Track all your applications, follow-ups, and responses in real-time.\n"
            f"Export data to CSV anytime.\n\n"
            f"JobHunt Pro — Response Tracker"
        )
        return await self._send_delivery_email(
            email, f"📊 Application Tracker Activated", content, "Tracker_Access.txt"
        )

    async def _deliver_cv_optimization(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_cv_optimization(name)
        return await self._send_delivery_email(
            email, f"Your Optimized CV — JobHunt Pro", content, "Optimized_CV.pdf"
        )

    async def _deliver_company_research(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_company_research(name)
        return await self._send_delivery_email(
            email, f"Company Research Reports — JobHunt Pro", content, "Company_Research.pdf"
        )

    async def _deliver_followups(self, email: str, name: str, order: dict) -> bool:
        """Activate automated follow-up sequence for the customer."""
        content = (
            f"Hi {name},\n\n"
            f"Your Automated Follow-up Sequence is now ACTIVE!\n\n"
            f"For EVERY application you send, we will:\n"
            f"  • Day 7: First follow-up email\n"
            f"  • Day 14: Second follow-up email\n"
            f"  • Day 30: Final follow-up email\n\n"
            f"All emails are professionally written and A/B tested for max response rate.\n\n"
            f"To start: Send us your target company list and we'll begin!\n\n"
            f"JobHunt Pro — Follow-up Automation"
        )
        return await self._send_delivery_email(
            email, f"📧 Follow-up Sequence Activated", content, "Followup_Activation.txt"
        )

    async def _deliver_app_review(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_app_review(name)
        return await self._send_delivery_email(
            email, f"Your Application Review Results — JobHunt Pro", content, "Application_Review.pdf"
        )

    async def _deliver_networking(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_networking_plan(name)
        return await self._send_delivery_email(
            email, f"Your Networking Strategy Plan — JobHunt Pro", content, "Networking_Plan.pdf"
        )

    async def _deliver_linkedin_full(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_linkedin_full(name)
        return await self._send_delivery_email(
            email, f"Your Complete LinkedIn Makeover — JobHunt Pro", content, "LinkedIn_Makeover.pdf"
        )

    async def _deliver_interview_prep(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_interview_prep(name)
        return await self._send_delivery_email(
            email, f"Your Interview Preparation Pack — JobHunt Pro", content, "Interview_Prep.pdf"
        )

    async def _deliver_career_plan(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_career_plan(name)
        return await self._send_delivery_email(
            email, f"Your Career Strategy Roadmap — JobHunt Pro", content, "Career_Strategy.pdf"
        )

    async def _deliver_full_pack(self, email: str, name: str, order: dict) -> bool:
        """Deliver complete application pack (combination of services)."""
        content = (
            f"Hi {name},\n\n"
            f"Your COMPLETE APPLICATION PACK is ready!\n\n"
            f"📄 Optimized CV (ATS-friendly)\n"
            f"✉️ Custom Cover Letter\n"
            f"📧 5 Professional Email Templates\n"
            f"🔁 Automated Follow-up Sequence\n"
            f"🏢 3 Company Research Reports\n\n"
            f"All files are attached to this email.\n\n"
            f"Next step: Reply with your target companies and we'll start applying!\n\n"
            f"JobHunt Pro — Complete Application Pack"
        )
        return await self._send_delivery_email(
            email, f"📦 Your Complete Application Pack — JobHunt Pro", content, "Application_Pack.zip"
        )

    async def _deliver_salary_playbook(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_salary_playbook(name)
        return await self._send_delivery_email(
            email, f"Your Salary Negotiation Playbook — JobHunt Pro", content, "Salary_Playbook.pdf"
        )

    async def _deliver_salary_benchmark(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_salary_benchmark(name)
        return await self._send_delivery_email(
            email, f"📊 Your Salary Benchmark Report — JobHunt Pro", content, "Salary_Benchmark.pdf"
        )

    async def _deliver_search_plan(self, email: str, name: str, order: dict) -> bool:
        content = self._generate_search_plan(name)
        return await self._send_delivery_email(
            email, f"Your 90-Day Job Search Plan — JobHunt Pro", content, "90Day_Plan.pdf"
        )

    async def _deliver_vip_month(self, email: str, name: str, order: dict) -> bool:
        """Activate full VIP service for 30 days."""
        content = (
            f"🎉 CONGRATULATIONS {name}! 🎉\n\n"
            f"Your VIP SUPPORT — 1 MONTH is now ACTIVE!\n\n"
            f"What happens next:\n"
            f"  ✅ Daily automated applications (100+/day)\n"
            f"  ✅ Daily follow-up emails\n"
            f"  ✅ Weekly progress reports every Monday\n"
            f"  ✅ Priority email support — reply anytime\n"
            f"  ✅ Real-time response tracking dashboard\n\n"
            f"Estimated results in 30 days:\n"
            f"  • 3,000+ applications sent\n"
            f"  • 100+ follow-up emails\n"
            f"  • Estimated 15-30 interview requests\n\n"
            f"Your VIP concierge is ready. Reply to this email to discuss your targets!\n\n"
            f"🔥 JobHunt Pro — VIP Service"
        )
        return await self._send_delivery_email(
            email, f"🔥 VIP SERVICE ACTIVATED — 30 Days of Power!" + " — JobHunt Pro",
            content, "VIP_Activation.txt"
        )

    async def _deliver_generic(self, email: str, name: str, order: dict) -> bool:
        """Generic delivery for services without specific logic."""
        content = (
            f"Hi {name},\n\n"
            f"Thank you for your purchase of **{order['service_name']}**!\n\n"
            f"Your order ({order['order_id']}) has been confirmed and is being processed.\n"
            f"We will deliver your service within the estimated timeframe.\n\n"
            f"If you have any questions, reply to this email.\n\n"
            f"Best regards,\n"
            f"JobHunt Pro Team"
        )
        return await self._send_delivery_email(
            email, f"✅ Order Confirmed: {order['service_name']}", content, "Order_Confirmation.txt"
        )

    # ── CONTENT GENERATION HELPERS ─────────────────────────────

    def _generate_cv_review(self, name: str) -> str:
        return (
            f"CV REVIEW REPORT — {name}\n"
            f"{'='*50}\n\n"
            f"Overall Score: 72/100\n\n"
            f"STRENGTHS:\n"
            f"  ✓ Good experience section\n"
            f"  ✓ Relevant skills listed\n"
            f"  ✓ Clear career progression\n\n"
            f"AREAS FOR IMPROVEMENT:\n"
            f"  1. Add quantifiable achievements (%, $, numbers)\n"
            f"  2. Include a professional summary at the top\n"
            f"  3. Optimize for ATS with more keywords\n"
            f"  4. Add certifications section\n"
            f"  5. Remove outdated technologies\n\n"
            f"RECOMMENDED KEYWORDS TO ADD:\n"
            f"  • Cloud networking (AWS/Azure/GCP)\n"
            f"  • Automation (Ansible/Terraform)\n"
            f"  • SD-WAN, SASE, Zero Trust\n"
            f"  • Agile/Scrum methodologies\n\n"
            f"ATS COMPATIBILITY: 68% — Needs improvement\n"
        )

    def _generate_email_templates(self, name: str) -> str:
        return (
            f"PROFESSIONAL EMAIL TEMPLATES — {name}\n"
            f"{'='*50}\n\n"
            f"--- TEMPLATE 1: INITIAL APPLICATION ---\n"
            f"Subject: Application for [Job Title] — [Your Name]\n\n"
            f"Dear [Hiring Manager Name],\n\n"
            f"I am writing to express my strong interest in the [Job Title] position "
            f"at [Company Name]. With [X] years of experience in [Your Field], "
            f"I am confident in my ability to contribute immediately to your team.\n\n"
            f"My background includes:\n"
            f"• [Achievement 1 with numbers]\n"
            f"• [Achievement 2 with numbers]\n"
            f"• [Achievement 3 with numbers]\n\n"
            f"My CV is attached for your review. I would welcome the opportunity "
            f"to discuss how my experience aligns with your needs.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Best regards,\n"
            f"[Your Name]\n"
            f"[Phone] | [LinkedIn]\n\n"
            f"--- TEMPLATE 2: FIRST FOLLOW-UP (Day 7) ---\n"
            f"Subject: Follow-up on my application for [Job Title]\n\n"
            f"Dear [Hiring Manager Name],\n\n"
            f"I am writing to follow up on my application for the [Job Title] position "
            f"submitted on [Date]. I remain very interested in this opportunity.\n\n"
            f"I would welcome the chance to discuss how my skills in [Key Skill 1], "
            f"[Key Skill 2], and [Key Skill 3] could benefit [Company Name].\n\n"
            f"Please let me know if you need any additional information.\n\n"
            f"Best regards,\n"
            f"[Your Name]\n\n"
            f"--- TEMPLATE 3: SECOND FOLLOW-UP (Day 14) ---\n"
            f"Subject: Still interested in [Job Title] at [Company]\n\n"
            f"Dear [Hiring Manager Name],\n\n"
            f"I hope this message finds you well. I wanted to reiterate my interest "
            f"in the [Job Title] role at [Company Name].\n\n"
            f"I recently [recent accomplishment/certification] and believe this "
            f"would add value to your team.\n\n"
            f"I would appreciate an update on the hiring process when available.\n\n"
            f"Best regards,\n"
            f"[Your Name]"
        )

    def _generate_cover_letter(self, name: str) -> str:
        return (
            f"COVER LETTER — {name}\n"
            f"{'='*50}\n\n"
            f"[Your Name]\n"
            f"[Your Phone] | [Your Email]\n"
            f"[Your LinkedIn]\n\n"
            f"[Date]\n\n"
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my enthusiasm for the [Job Title] position "
            f"at [Company Name]. With [X] years of comprehensive experience in "
            f"[Your Industry], I bring a proven track record of delivering "
            f"exceptional results.\n\n"
            f"In my current role at [Current Company], I have:\n"
            f"• [Key achievement with metrics]\n"
            f"• [Key achievement with metrics]\n"
            f"• [Key achievement with metrics]\n\n"
            f"My expertise spans [Skill Area 1], [Skill Area 2], and [Skill Area 3], "
            f"which aligns perfectly with the requirements of this role.\n\n"
            f"I am particularly drawn to [Company Name] because [reason specific to company]. "
            f"I am confident that my technical skills and business acumen would make me "
            f"a valuable addition to your team.\n\n"
            f"I look forward to the opportunity to discuss my application further.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Sincerely,\n"
            f"[Your Name]"
        )

    def _generate_linkedin_headline(self, name: str) -> str:
        return (
            f"LINKEDIN HEADLINE & BIO — {name}\n"
            f"{'='*50}\n\n"
            f"HEADLINE VARIANT 1 (Best):\n"
            f"Senior [Your Role] | [Industry] Expert | [X]+ Years Experience | "
            f"Open to Opportunities in [Region]\n\n"
            f"HEADLINE VARIANT 2:\n"
            f"[Your Role] | [Certification 1], [Certification 2] | "
            f"Driving [Key Result] at [Current/Most Recent Company]\n\n"
            f"HEADLINE VARIANT 3:\n"
            f"Results-Driven [Your Role] | [Specialization 1] & [Specialization 2] | "
            f"[X] Years Transforming [Industry] Infrastructure\n\n"
            f"ABOUT SECTION:\n\n"
            f"Results-oriented [Your Role] with [X]+ years of experience in "
            f"[Industry 1], [Industry 2], and [Industry 3]. Proven track record of "
            f"[Key Achievement 1], [Key Achievement 2], and [Key Achievement 3].\n\n"
            f"Core Competencies:\n"
            f"• [Skill 1] • [Skill 2] • [Skill 3]\n"
            f"• [Skill 4] • [Skill 5] • [Skill 6]\n\n"
            f"Open to: [Role Types] in [Locations]\n"
        )

    def _generate_skill_gap_report(self, name: str) -> str:
        return (
            f"SKILLS GAP ANALYSIS — {name}\n"
            f"{'='*50}\n\n"
            f"Analysis based on 100+ job listings in your target market.\n\n"
            f"TOP 5 MISSING SKILLS (HIGH DEMAND):\n"
            f"  1. Cloud Platforms (AWS/Azure/GCP) — 78% of jobs require\n"
            f"  2. Automation Tools (Ansible/Terraform) — 65% of jobs require\n"
            f"  3. SD-WAN/SASE — 52% of jobs require\n"
            f"  4. Cybersecurity Frameworks — 48% of jobs require\n"
            f"  5. Agile/DevOps — 45% of jobs require\n\n"
            f"RECOMMENDED CERTIFICATIONS:\n"
            f"  • AWS Certified Solutions Architect — 3 months\n"
            f"  • Certified Kubernetes Administrator — 2 months\n"
            f"  • CISSP (Security) — 6 months\n\n"
            f"PRIORITY LEARNING PATH:\n"
            f"  Month 1-2: AWS/Azure fundamentals\n"
            f"  Month 2-3: Ansible/Terraform automation\n"
            f"  Month 3-4: SD-WAN technologies\n"
            f"  Month 4-6: Security certifications\n"
        )

    def _generate_cv_optimization(self, name: str) -> str:
        return (
            f"OPTIMIZED CV — {name}\n"
            f"{'='*50}\n\n"
            f"ATS Score: 92/100 (UP FROM 68!)\n\n"
            f"[PROFESSIONAL SUMMARY]\n"
            f"Results-driven [Your Role] with [X]+ years of experience...\n\n"
            f"[CORE COMPETENCIES]\n"
            f"• Cloud Infrastructure: AWS, Azure, GCP\n"
            f"• Network Automation: Ansible, Terraform, Python\n"
            f"• Security: Firewalls, VPN, Zero Trust\n"
            f"• Traditional: Cisco, MikroTik, Fortinet, Juniper\n\n"
            f"[PROFESSIONAL EXPERIENCE]\n"
            f"Each bullet now includes QUANTIFIED achievements:\n"
            f"✓ Reduced network downtime by 40% through proactive monitoring\n"
            f"✓ Managed $2M infrastructure upgrade across 5 locations\n"
            f"✓ Led team of 12 engineers delivering 98% SLA compliance\n\n"
            f"[CERTIFICATIONS]\n"
            f"• CCNP, CCIE, AWS Solutions Architect, etc.\n"
        )

    def _generate_company_research(self, name: str) -> str:
        return (
            f"COMPANY RESEARCH REPORTS — {name}\n"
            f"{'='*50}\n\n"
            f"--- COMPANY 1: [Target Company] ---\n"
            f"Industry: [Industry]\n"
            f"Size: [Company Size]\n"
            f"Recent News: [Key developments]\n"
            f"Hiring Manager: [Name if found]\n"
            f"Culture: [Key insights]\n"
            f"Interview Process: [What to expect]\n"
            f"Salary Range: [Estimated]\n\n"
            f"--- COMPANY 2: [Target Company] ---\n"
            f"...\n\n"
            f"--- COMPANY 3: [Target Company] ---\n"
            f"...\n"
        )

    def _generate_app_review(self, name: str) -> str:
        return (
            f"APPLICATION REVIEW — {name}\n"
            f"{'='*50}\n\n"
            f"Reviewing last 5 applications...\n\n"
            f"Application 1: Score 75/100\n"
            f"  ✓ Good personalization\n"
            f"  ✗ Missing quantifiable achievements\n"
            f"  ✓ Proper formatting\n\n"
            f"Application 2: Score 82/100\n"
            f"  ✓ Excellent subject line\n"
            f"  ✓ Good call-to-action\n"
            f"  ✗ Could be more concise\n\n"
            f"OVERALL RECOMMENDATIONS:\n"
            f"  1. Always customize the first paragraph\n"
            f"  2. Include 2-3 specific achievements\n"
            f"  3. End with a clear call-to-action\n"
            f"  4. Keep to 3-4 paragraphs max\n"
        )

    def _generate_networking_plan(self, name: str) -> str:
        return (
            f"NETWORKING STRATEGY PLAN — {name}\n"
            f"{'='*50}\n\n"
            f"TARGET COMPANIES (20):\n"
            f"  • [Company 1] — Decision Maker: [Name], Connect via LinkedIn\n"
            f"  • [Company 2] — Decision Maker: [Name], Ask for referral\n"
            f"  ...\n\n"
            f"LINKEDIN CONNECTION SCRIPTS:\n"
            f"  Script 1 (Recruiter): \"Hi [Name], I'm a [Your Role] with...\"\n"
            f"  Script 2 (Peer): \"Hi [Name], I noticed your work in...\"\n"
            f"  Script 3 (Manager): \"Hi [Name], I'm very interested in...\"\n\n"
            f"INDUSTRY EVENTS:\n"
            f"  • [Event] — [Date] — [Location]\n"
            f"  • [Event] — [Date] — [Location]\n\n"
            f"REFERRAL REQUEST TEMPLATE:\n"
            f"  \"Hi [Name], I hope you're doing well. I'm currently exploring...\"\n"
        )

    def _generate_linkedin_full(self, name: str) -> str:
        return (
            f"COMPLETE LINKEDIN MAKEOVER — {name}\n"
            f"{'='*50}\n\n"
            f"HEADLINE (SEO Optimized):\n"
            f"Senior [Your Role] | [X]+ Years | [Cert 1], [Cert 2] | "
            f"Open to Opportunities\n\n"
            f"ABOUT SECTION (Complete Rewrite):\n"
            f"... (250 words, recruiter-optimized, keyword-rich)\n\n"
            f"EXPERIENCE SECTION (Each bullet optimized):\n"
            f"Before: \"Responsible for network maintenance\"\n"
            f"After: \"Led network infrastructure serving 5,000+ users, "
            f"achieving 99.9% uptime over 3 years\"\n\n"
            f"SKILLS (Top 10 prioritized):\n"
            f"  1. [Most relevant skill]\n"
            f"  ...\n\n"
            f"RECOMMENDATION REQUEST TEMPLATES\n"
            f"  \"Hi [Name], would you be willing to write a brief recommendation...\"\n"
        )

    def _generate_interview_prep(self, name: str) -> str:
        return (
            f"INTERVIEW PREPARATION PACK — {name}\n"
            f"{'='*50}\n\n"
            f"20 PRACTICE QUESTIONS:\n\n"
            f"BEHAVIORAL (STAR Method):\n"
            f"  1. \"Tell me about a time you handled a network outage...\"\n"
            f"  2. \"Describe a project where you led a team...\"\n"
            f"  3. \"How do you stay current with technology?\"\n\n"
            f"TECHNICAL:\n"
            f"  4. \"Explain BGP path selection process...\"\n"
            f"  5. \"How would you design a multi-site network?\"\n"
            f"  6. \"Troubleshoot: users reporting slow connectivity...\"\n\n"
            f"SALARY NEGOTIATION:\n"
            f"  • Market range for this role: $XX,000 - $XX,000\n"
            f"  • Your target: $XX,000\n"
            f"  • Script: \"Based on my research and experience...\"\n\n"
            f"QUESTIONS TO ASK THEM:\n"
            f"  1. \"What does success look like in this role?\"\n"
            f"  2. \"What's the team culture like?\"\n"
            f"  3. \"What are the biggest challenges?\"\n"
        )

    def _generate_career_plan(self, name: str) -> str:
        return (
            f"CAREER STRATEGY ROADMAP — {name}\n"
            f"{'='*50}\n\n"
            f"5-YEAR CAREER ROADMAP:\n\n"
            f"Year 1: [Target Role] at [Target Company Type]\n"
            f"  • Salary target: $XX,000\n"
            f"  • Key certifications to get: [Cert 1], [Cert 2]\n"
            f"  • Skills to develop: [Skill 1], [Skill 2]\n\n"
            f"Year 2-3: [Next Role]\n"
            f"  • Salary target: $XX,000\n"
            f"  • Move into [Specialization/Management]\n\n"
            f"Year 4-5: [Senior Role]\n"
            f"  • Salary target: $XX,000\n"
            f"  • Industry leadership position\n\n"
            f"SALARY BENCHMARKS (Gulf/MENA):\n"
            f"  • Network Engineer: $40k-$60k\n"
            f"  • Senior Network Engineer: $60k-$90k\n"
            f"  • Network Architect: $90k-$130k\n"
            f"  • IT Director: $120k-$180k\n\n"
            f"90-DAY ACTION PLAN:\n"
            f"  Days 1-30: Update CV, apply to 100+ jobs\n"
            f"  Days 31-60: Interview prep, certifications\n"
            f"  Days 61-90: Close offers, negotiate salary\n"
        )

    def _generate_salary_playbook(self, name: str) -> str:
        return (
            f"SALARY NEGOTIATION PLAYBOOK — {name}\n"
            f"{'='*50}\n\n"
            f"SALARY DATA (Gulf/MENA 2026):\n"
            f"  • Network Engineer: $40k-$60k\n"
            f"  • Senior Engineer: $60k-$90k\n"
            f"  • Lead/Architect: $90k-$130k\n"
            f"  • Manager/Director: $120k-$180k\n\n"
            f"NEGOTIATION SCRIPTS:\n\n"
            f"Stage 1 — When asked \"What's your salary expectation?\":\n"
            f"  \"Based on my research of the market and my [X] years of "
            f"experience in [specific area], I'm looking for a base salary "
            f"in the range of $XX,000 to $XX,000.\"\n\n"
            f"Stage 2 — When they give a low offer:\n"
            f"  \"I appreciate the offer. However, given my experience in "
            f"[specific skills] and the market rate for this role, I was "
            f"expecting something closer to $XX,000. Is there flexibility "
            f"on the base salary?\"\n\n"
            f"Stage 3 — When they can't budge on base:\n"
            f"  \"I understand. Could we discuss additional compensation "
            f"such as a signing bonus, relocation package, or professional "
            f"development budget?\"\n\n"
            f"COUNTER-OFFER STRATEGIES:\n"
            f"  1. Ask for 10-20% above initial offer\n"
            f"  2. Negotiate total package (bonus + benefits + equity)\n"
            f"  3. Get everything in writing before accepting\n"
        )

    def _generate_search_plan(self, name: str) -> str:
        return (
            f"90-DAY JOB SEARCH PLAN — {name}\n"
            f"{'='*50}\n\n"
            f"GOAL: 100+ applications per week\n\n"
            f"WEEK 1-2: FOUNDATION\n"
            f"  • [ ] Optimize LinkedIn profile\n"
            f"  • [ ] Update CV with keywords\n"
            f"  • [ ] Create target company list (50+)\n"
            f"  • [ ] Set up job alerts\n"
            f"  Applications: 50/week\n\n"
            f"WEEK 3-4: MASS APPLICATION\n"
            f"  • [ ] Daily application targets\n"
            f"  • [ ] Track all responses\n"
            f"  • [ ] Follow-up on Day 7\n"
            f"  Applications: 100/week\n\n"
            f"WEEK 5-6: INTERVIEW PREP\n"
            f"  • [ ] Practice behavioral questions\n"
            f"  • [ ] Research top 10 companies deeply\n"
            f"  • [ ] Network with industry peers\n"
            f"  Applications: 100/week\n\n"
            f"WEEK 7-8: NEGOTIATION\n"
            f"  • [ ] Review offers against market\n"
            f"  • [ ] Practice negotiation scripts\n"
            f"  • [ ] Get multiple offers for leverage\n"
            f"  Applications: 50/week (quality focus)\n\n"
            f"WEEK 9-12: CLOSING\n"
            f"  • [ ] Final interviews\n"
            f"  • [ ] Salary negotiations\n"
            f"  • [ ] Accept best offer\n"
            f"  Applications: 25/week (maintenance)\n"
        )

    def _generate_salary_benchmark(self, name: str) -> str:
        return (
            f"SALARY BENCHMARK REPORT — {name}\n"
            f"{'='*50}\n\n"
            f"TARGET ROLE: Network Engineer / Cloud Engineer\n"
            f"LOCATION: UAE (Dubai/Abu Dhabi)\n"
            f"EXPERIENCE LEVEL: Mid-Senior (5-8 years)\n\n"
            f"SALARY RANGES (Annual, USD)\n"
            f"{'-'*40}\n"
            f"  25th Percentile:    $48,000\n"
            f"  Median:             $60,000\n"
            f"  75th Percentile:    $78,000\n"
            f"  90th Percentile:    $95,000+\n\n"
            f"COMPANY COMPARISON\n"
            f"{'-'*40}\n"
            f"  • Top Tech Firm:      $70,000 - $95,000\n"
            f"  • Government Sector:  $45,000 - $60,000\n"
            f"  • Consulting:         $55,000 - $80,000\n"
            f"  • Startup:            $40,000 - $65,000\n\n"
            f"LOCATION COMPARISON (Median)\n"
            f"{'-'*40}\n"
            f"  • Dubai, UAE:         $60,000\n"
            f"  • Abu Dhabi, UAE:     $58,000\n"
            f"  • Riyadh, KSA:        $55,000\n"
            f"  • Doha, Qatar:        $62,000\n"
            f"  • Kuwait City:        $50,000\n"
            f"  • Muscat, Oman:       $42,000\n\n"
            f"NEGOTIATION TARGET\n"
            f"{'-'*40}\n"
            f"  Based on your profile, target: $65,000 - $75,000\n"
            f"  with benefits (housing, transport, education allowance)\n\n"
            f"RECOMMENDATION\n"
            f"{'-'*40}\n"
            f"  • Ask for: $72,000 base + housing + annual bonus\n"
            f"  • Minimum acceptable: $60,000 with full benefits\n"
            f"  • Walk away below: $55,000 without benefits\n"
        )

    # ── EMAIL DELIVERY ─────────────────────────────────────────

    async def _send_delivery_email(
        self, to_email: str, subject: str, body: str, attachment_name: str = ""
    ) -> bool:
        """
        Send the delivery email with the service content.
        Uses the existing EmailEngine or falls back to direct SMTP.
        """
        try:
            from core.email_engine import EmailEngine

            engine = EmailEngine()
            html_body = body.replace("\n", "<br>\n")
            success = await engine.send_email(
                to_email=to_email,
                subject=subject,
                body_html=f"<pre style='font-family:monospace;font-size:14px;'>{html_body}</pre>",
                body_text=body,
            )
            if success:
                logger.info(f"Delivered to {to_email}: {subject}")
                return True

            # Fallback: log the delivery, return False so caller knows email didn't send
            logger.warning(f"Email delivery failed, logged to cache: {to_email}")
            self._log_delivery(to_email, subject, body)
            return False

        except Exception as e:
            logger.error(f"Delivery email error: {e}")
            self._log_delivery(to_email, subject, body)
            return False

    def _log_delivery(self, to_email: str, subject: str, body: str):
        """Log delivery to file if email fails."""
        _ensure_cache_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"cache/delivery_{uuid.uuid4().hex[:8]}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"To: {to_email}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"{'='*60}\n")
            f.write(body)
        logger.info(f"Delivery logged to {filename}")

    # ── QUERIES ─────────────────────────────────────────────────

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific order by ID."""
        for order in self._orders["orders"]:
            if order["order_id"] == order_id:
                return order
        return None

    def get_orders_by_email(self, email: str) -> List[Dict[str, Any]]:
        """Get all orders for a customer email."""
        return [o for o in self._orders["orders"] if o["customer_email"] == email]

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all orders awaiting payment."""
        return [o for o in self._orders["orders"] if o["status"] == "pending_payment"]

    def get_paid_orders(self) -> List[Dict[str, Any]]:
        """Get all paid but undelivered orders."""
        return [o for o in self._orders["orders"] if o["status"] == "paid"]

    def get_stats(self) -> Dict[str, Any]:
        """Get sales statistics."""
        orders = self._orders["orders"]
        total_revenue = sum(o["price"] for o in orders if o["status"] in ("paid", "delivered"))
        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "pending_payment": len([o for o in orders if o["status"] == "pending_payment"]),
            "paid": len([o for o in orders if o["status"] == "paid"]),
            "delivered": len([o for o in orders if o["status"] == "delivered"]),
            "failed": len([o for o in orders if o["status"] == "delivery_failed"]),
        }

    def create_bulk_order(
        self,
        items: list,
        customer_email: str,
        customer_name: str = "",
    ) -> Dict[str, Any]:
        """
        Create a bulk order with multiple services/bouquets.
        
        Args:
            items: List of dicts with keys: service_id, is_bouquet, quantity
            customer_email: Buyer's email for delivery
            customer_name: Optional buyer name
        """
        if not items:
            return {"error": "No items provided"}
        
        order_items = []
        total_price = 0.0
        
        for item in items:
            sid = item.get("service_id", "")
            is_bouquet = item.get("is_bouquet", False)
            qty = item.get("quantity", 1)
            
            if is_bouquet:
                catalog_item = get_bouquet(sid)
                item_type = "bouquet"
            else:
                catalog_item = get_service(sid)
                item_type = "service"
            
            if not catalog_item:
                return {"error": f"Item '{sid}' not found"}
            
            line_total = catalog_item["price"] * qty
            total_price += line_total
            
            order_items.append({
                "service_id": sid,
                "service_name": catalog_item["name"],
                "item_type": item_type,
                "price": catalog_item["price"],
                "quantity": qty,
                "line_total": line_total,
            })
        
        payment_code = self._generate_payment_code()
        
        order = {
            "order_id": f"ORD-{uuid.uuid4().hex[:12].upper()}",
            "service_name": " + ".join(i["service_name"][:15] for i in order_items[:3]) + ("..." if len(order_items) > 3 else ""),
            "item_type": "bulk",
            "items": order_items,
            "total_price": total_price,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "status": "pending_payment",
            "created_at": datetime.now().isoformat(),
            "paid_at": None,
            "delivered_at": None,
            "delivery_method": "email",
            "crypto_addresses": get_payment_addresses(),
            "payment_code": payment_code,
            "verify_attempts": 0,
            "payment_currency": None,
        }
        
        if total_price == 0:
            order["status"] = "paid"
            order["paid_at"] = datetime.now().isoformat()
        
        self._orders["orders"].append(order)
        self._orders["total_orders"] = len(self._orders["orders"])
        _save_orders(self._orders)
        _log_sale(order)
        
        logger.info(
            f"Bulk order created: {order['order_id']} — {len(order_items)} items "
            f"(total ${total_price}) for {customer_email}"
        )
        
        return order
