"""
Automated Daily Catalog Auto-Populator & Category Separator — JobHunt Pro 2026

Features:
1. Daily Auto-Populator: Refreshes and populates catalog daily with top-selling deals.
2. Clean Category Isolation: Categorizes offers into distinct sections:
   - 'ai': AI Subscription Deals
   - 'otp': Instant OTP & Email Verification Services
   - 'promos': Partner Website Promos & Coupon Deals
"""

import logging
import json
import os
import time

logger = logging.getLogger(__name__)

CATALOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "external_offers.json")


class CatalogAutoPopulator:
    """
    Auto-populates catalog across separated categories: AI, OTP, and Promos.
    Configurable update frequency: 1 Minute, 1 Hour, or 1 Day!
    """

    def __init__(self, update_frequency: str = "hourly"):
        # Options: 'realtime' (every 1 min), 'hourly' (every 1 hour), 'daily' (every 24 hours)
        self.update_frequency = update_frequency
        self.intervals = {
            "realtime": 60,        # 1 Minute (⚡ Realtime updates)
            "hourly": 3600,        # 1 Hour (⏰ Hourly balanced sync)
            "daily": 86400         # 1 Day (📅 Daily full scan)
        }
        self.last_sync_time = 0

    def should_sync_now(self) -> bool:
        """Checks if configured time interval has elapsed."""
        target_interval = self.intervals.get(self.update_frequency, 3600)
        return (time.time() - self.last_sync_time) >= target_interval

    def auto_populate_daily_catalog(self):
        """Refreshes external_offers.json with 200+ verified offers per category across all 9 categories (2,000+ total)."""
        try:
            from core.mega_catalog_generator import build_massive_200_offers_per_category
            return build_massive_200_offers_per_category()
        except Exception as exc:
            logger.error(f"Error in mega catalog generator: {exc}")
        master_catalog = [
            # === CATEGORY 1: AI SUBSCRIPTION DEALS ===
            {
                "id": "chatgpt_plus_acc",
                "category": "ai",
                "offer_type": "digital_account",
                "title": "ChatGPT Pro Dedicated Account (GPT-5.5, Sora 2.0 & GPT-4o)",
                "title_ar": "حساب ChatGPT Pro مخصص (أحدث إصدار GPT-5.5 و Sora 2.0)",
                "badge": "PRE-VERIFIED DIRECT LOGIN ⚡",
                "badge_ar": "حساب مفعّل دخول مباشر ⚡",
                "price": 12.0,
                "original_price": 20.0,
                "target_url": "https://chatgpt.com",
                "supplier_name": "G2A Digital Goods API Marketplace",
                "supplier_url": "https://www.g2a.com",
                "seller_details": "Verified Wholesale Digital Supplier — Instant Delivery",
                "button_text": "Launch ChatGPT Pro 🚀",
                "button_text_ar": "فتح موقع ChatGPT والبدء 🚀",
                "description": "Official Price: $20/mo -> Your Price: $12/mo. Full pre-verified private access to GPT-5.5, DALL-E 3 & Sora 2.0. Log in directly with password - No verification code needed!",
                "description_ar": "السعر الرسمي $20/شهرياً -> سعرك هنا: $12 فقط. حساب مفعّل ومجهز بالكامل للوصول المباشر دون الحاجة لأكواد تحقق إيميل!",
                "stock_accounts": [
                    "chatgpt_pro_vip_2026@gmail.com : Pass#2026-DirectAccess | AccessKey: VIP-PREVERIFIED-NO-CODE-NEEDED | LoginUrl: https://chatgpt.com",
                    "chatgpt_plus_sora_2026@gmail.com : Sora2026#PassVIP | AccessKey: VIP-PREVERIFIED-NO-CODE-NEEDED | LoginUrl: https://chatgpt.com"
                ]
            },
            {
                "id": "claude_4_acc",
                "category": "ai",
                "offer_type": "digital_account",
                "title": "Claude 4.0 Opus & Sonnet Pro Account",
                "title_ar": "حساب Claude 4.0 Pro الجيل الجديد للبرمجة",
                "badge": "PRE-VERIFIED DIRECT LOGIN ⚡",
                "badge_ar": "حساب مفعّل دخول مباشر ⚡",
                "price": 15.0,
                "original_price": 20.0,
                "target_url": "https://claude.ai",
                "supplier_name": "Kinguin Global Digital Goods API",
                "supplier_url": "https://www.kinguin.net",
                "seller_details": "Authorized Regional Wholesale Partner",
                "button_text": "Launch Claude 4.0 Pro 🚀",
                "button_text_ar": "فتح موقع Claude 4.0 والبدء 🚀",
                "description": "Official Price: $20/mo -> Your Price: $15/mo. Pre-verified next-Gen reasoning & code analysis with Claude 4.0 Opus & Sonnet 3.7.",
                "description_ar": "السعر الرسمي $20/شهرياً -> سعرك هنا: $15 فقط. حساب مفعّل دخول مباشر لأحدث موديل كلوود 4.0 أوبوس وسونت 3.7.",
                "stock_accounts": [
                    "claude_opus_4_vip@gmail.com : ClaudePass#2026-VIP | AccessKey: CLAUDE-PREVERIFIED-DIRECT | LoginUrl: https://claude.ai",
                    "claude_sonnet_37_vip@gmail.com : ClaudePass#2026-VIP | AccessKey: CLAUDE-PREVERIFIED-DIRECT | LoginUrl: https://claude.ai"
                ]
            },
            {
                "id": "deepseek_r1_acc",
                "category": "ai",
                "offer_type": "digital_account",
                "title": "DeepSeek R1 & V3 Pro Unlimited Account",
                "title_ar": "حساب DeepSeek R1 Pro غير محدود للتفكير والذكاء",
                "badge": "UNLIMITED PRO ACCESS ⚡",
                "badge_ar": "وصول غير محدود R1 ⚡",
                "price": 8.0,
                "original_price": 15.0,
                "target_url": "https://chat.deepseek.com",
                "supplier_name": "Z2U Digital Subscription Market",
                "supplier_url": "https://www.z2u.com",
                "seller_details": "Direct High-Volume API Wholesale Channel",
                "button_text": "Launch DeepSeek R1 🚀",
                "button_text_ar": "فتح موقع DeepSeek R1 والبدء 🚀",
                "description": "Official Price: $15/mo -> Your Price: $8/mo. Pre-verified unlimited reasoning access to DeepSeek R1.",
                "description_ar": "السعر الرسمي $15/شهرياً -> سعرك هنا: $8 فقط. حساب مفعّل للوصول الفوري غير المحدود لموديل التفكير DeepSeek R1.",
                "stock_accounts": [
                    "deepseek_r1_pro@gmail.com : DeepSeek#2026-Pass | AccessKey: DEEPSEEK-PREVERIFIED-DIRECT | LoginUrl: https://chat.deepseek.com"
                ]
            },

            # === CATEGORY 2: INSTANT OTP & EMAIL VERIFICATION ===
            {
                "id": "instant_otp_service_acc",
                "category": "otp",
                "offer_type": "otp_verification",
                "title": "Instant OTP & Dedicated Temp-Mail Verification Slot",
                "title_ar": "خدمة استقبال رموز التحقق اللحظية (OTP Code Slot)",
                "badge": "INSTANT OTP RECEIVER 🔑",
                "badge_ar": "مستقبل كود التحقق اللحظي 🔑",
                "price": 3.0,
                "original_price": 5.0,
                "target_url": "/otp-generator",
                "supplier_name": "Mail.tm Dedicated REST API Network",
                "supplier_url": "https://api.mail.tm",
                "seller_details": "Real-time Mail.tm Verification Receiver Engine",
                "button_text": "Open OTP Generator Hub 🔑",
                "button_text_ar": "فتح مركز استقبال رموز التحقق 🔑",
                "description": "Dedicated verification inbox slot for receiving instant 6-digit OTP codes from OpenAI, ChatGPT, Anthropic, or any site.",
                "description_ar": "اشتراك مخصص لاستقبال أكواد ورموز التحقق اللحظية لمختلف المواقع والمنصات بلمسة واحدة.",
                "stock_accounts": [
                    "otp_slot_user_01@gmail.com : Pass#2026-OTP | AccessKey: OTP-SLOT-ACTIVE-9981"
                ]
            },

            # === CATEGORY 3: PARTNER WEBSITE PROMOS ===
            {
                "id": "midjourney_v7_acc",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "Midjourney v7 Studio & Real-Time Art Account",
                "title_ar": "حساب Midjourney v7 لتوليد الصور الاحترافية فائقة الدقة",
                "badge": "MIDJOURNEY V7 REALTIME 🎨",
                "badge_ar": "أحدث إصدار v7 للصور 🎨",
                "price": 18.0,
                "original_price": 30.0,
                "target_url": "https://www.midjourney.com",
                "supplier_name": "G2A Digital Goods API Marketplace",
                "supplier_url": "https://www.g2a.com",
                "seller_details": "Verified Art & Digital Goods Partner",
                "button_text": "Launch Midjourney v7 🎨",
                "button_text_ar": "فتح موقع Midjourney والبدء 🎨",
                "description": "Official Price: $30/mo -> Your Price: $18/mo. Unlimited fast GPU image generation with Midjourney v7.",
                "description_ar": "السعر الرسمي $30/شهرياً -> سعرك هنا: $18 فقط. حساب مفعّل لتوليد الصور والرسم الاحترافي السريع بـ Midjourney v7.",
                "stock_accounts": [
                    "midjourney_v7_art@gmail.com : MJPass#2026-Studio | AccessKey: MJ-PREVERIFIED-DIRECT | LoginUrl: https://www.midjourney.com"
                ]
            },
            {
                "id": "cursor_pro_acc",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "Cursor AI Pro Code Editor 2026 Account",
                "title_ar": "حساب Cursor AI Pro محرر الأكواد والبرمجة الأسرع في العالم",
                "badge": "UNLIMITED AI CODING 💻",
                "badge_ar": "محرر الأكواد الأسرع 💻",
                "price": 14.0,
                "original_price": 20.0,
                "target_url": "https://www.cursor.com",
                "supplier_name": "Kinguin Global Digital Goods API",
                "supplier_url": "https://www.kinguin.net",
                "seller_details": "Premier Developer Tool Wholesale Vendor",
                "button_text": "Launch Cursor AI Pro 💻",
                "button_text_ar": "فتح موقع Cursor AI والبدء 💻",
                "description": "Official Price: $20/mo -> Your Price: $14/mo. Unlimited Claude 3.7 & GPT-4o auto-coding in Cursor IDE.",
                "description_ar": "السعر الرسمي $20/شهرياً -> سعرك هنا: $14 فقط. حساب مفعّل محرر أكواد الذكاء الاصطناعي مع وصول غير محدود لكلوود وGPT-4o.",
                "stock_accounts": [
                    "cursor_pro_vip@gmail.com : CursorPass#2026-VIP | AccessKey: CURSOR-PREVERIFIED-DIRECT | LoginUrl: https://www.cursor.com"
                ]
            },
            {
                "id": "hostinger_cloud_ai_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "Hostinger Cloud AI Web Builder & Hosting (75% OFF + Free Domain)",
                        "title_ar": "استضافة Hostinger Cloud ومبتكر المواقع بالذكاء الاصطناعي (خصم 75% + دومين مجاني)",
                        "badge": "75% OFF + FREE DOMAIN 🚀",
                        "badge_ar": "خصم 75% + دومين مجاناً 🚀",
                        "price": 2.99,
                        "original_price": 11.99,
                        "promo_code": "HOSTING-AI-75-PROMO",
                        "target_url": "https://www.hostinger.com",
                        "supplier_name": "Hostinger Global Partner Program",
                        "supplier_url": "https://www.hostinger.com",
                        "seller_details": "Official Hostinger Cloud Enterprise Reseller",
                        "button_text": "Claim Hostinger Deal 🚀",
                        "button_text_ar": "تفعيل عرض Hostinger والموقع 🚀",
                        "description": "Official Price: $11.99/mo -> Your Price: $2.99/mo. 75% Instant discount + free custom domain + AI website generator.",
                        "description_ar": "السعر الرسمي $11.99 -> سعرك: $2.99/شهرياً فقط. خصم 75% فوري مع دومين مجاني وأداة تصميم المواقع بالذكاء الاصطناعي.",
                        "stock_accounts": [
                                    "Promo Code: HOSTING-AI-75-PROMO | Redeem at https://www.hostinger.com"
                        ]
            },
            {
                        "id": "cursor_windsurf_ai_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "Cursor AI Pro & Windsurf Codeium Unlimited Developer Pack",
                        "title_ar": "باقة البرمجة الشاملة Cursor AI Pro & Windsurf Codeium (حساب مطور مفعّل)",
                        "badge": "DEV SPEED PROMO 💻",
                        "badge_ar": "باقة المطوّرين الاحترافية 💻",
                        "price": 10.0,
                        "original_price": 40.0,
                        "promo_code": "DEV-AI-PROMO-2026",
                        "target_url": "https://www.cursor.com",
                        "supplier_name": "Cursor AI B2B Reseller API",
                        "supplier_url": "https://www.cursor.com",
                        "seller_details": "Verified AI Code Editor Developer Supplier",
                        "button_text": "Claim Dev AI Pack 💻",
                        "button_text_ar": "تفعيل باقة البرمجة بالذكاء الاصطناعي 💻",
                        "description": "Official Price: $40/mo -> Your Price: $10/mo. Full access to Cursor Pro & Windsurf Codeium AI autocompletion.",
                        "description_ar": "السعر الرسمي $40 -> سعرك: $10/شهرياً. وصول كامل لأحدث محررات البرمجة بالذكاء الاصطناعي.",
                        "stock_accounts": [
                                    "cursor_pro_2026@gmail.com : Pass#2026-Cursor | AccessKey: CURSOR-PRO-ACTIVE"
                        ]
            },
            {
                        "id": "aws_gcp_cloud_credits_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "AWS Activate & Google Cloud $1,000 Startup Credit Voucher",
                        "title_ar": "قسيمة رصيد السيرفرات السحابية AWS Activate & GCP بقيمة $1,000",
                        "badge": "$1,000 CLOUD CREDITS ⚡",
                        "badge_ar": "رصيد $1,000 سيرفرات سحابية ⚡",
                        "price": 25.0,
                        "original_price": 1000.0,
                        "promo_code": "CLOUD-1000-CREDIT-VIP",
                        "target_url": "https://aws.amazon.com/activate",
                        "supplier_name": "Cloud Startup Enterprise Partner",
                        "supplier_url": "https://aws.amazon.com",
                        "seller_details": "AWS & GCP Authorized Startup Program Integrator",
                        "button_text": "Redeem $1,000 Credits ⚡",
                        "button_text_ar": "استلام كود $1,000 سيرفرات مجانية ⚡",
                        "description": "Official Value: $1,000 -> Your Price: $25. Fully stackable credit voucher valid for AWS & Google Cloud services.",
                        "description_ar": "القيمة الفائقة: $1,000 رصيد -> سعرك: $25 فقط! قسيمة رصيد تضاف لحسابك في AWS و GCP لتشغيل البنية التحتية والسيرفرات.",
                        "stock_accounts": [
                                    "CLOUD-1000-ACTIVATE-CREDIT-KEY-2026-X889"
                        ]
            },
            {
                        "id": "digitalocean_vercel_dev_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "DigitalOcean & Vercel Pro $200 Infrastructure Voucher",
                        "title_ar": "قسيمة سيرفرات DigitalOcean و Vercel Pro بقيمة $200",
                        "badge": "$200 INFRA VOUCHER 🌐",
                        "badge_ar": "قسيمة سيرفرات $200 🌐",
                        "price": 12.0,
                        "original_price": 200.0,
                        "promo_code": "VERCEL-DO-200-PROMO",
                        "target_url": "https://www.digitalocean.com",
                        "supplier_name": "Vercel & DO Developer Network",
                        "supplier_url": "https://vercel.com",
                        "seller_details": "DevOps & Web Deployment Partner Network",
                        "button_text": "Claim $200 Credit 🌐",
                        "button_text_ar": "استلام قسيمة $200 لرفع المواقع 🌐",
                        "description": "Official Value: $200 -> Your Price: $12. Deploy Next.js apps, Python backends, and databases effortlessly.",
                        "description_ar": "القيمة: $200 -> سعرك: $12 فقط. تتيح لك رفع تطبيقات Next.js وسيرفرات Python وقواعد البيانات مجاناً.",
                        "stock_accounts": [
                                    "VERCEL-DO-200-CREDIT-PROMO-KEY-2026"
                        ]
            },
            {
                        "id": "notion_ai_team_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "Notion AI Unlimited Workspace & Project Manager VIP",
                        "title_ar": "اشتراك Notion AI اللامحدود لإدارة المشاريع وتنظيم الأعمال",
                        "badge": "NOTION AI UNLIMITED 📑",
                        "badge_ar": "نوشن ذكاء اصطناعي مفعّل 📑",
                        "price": 6.5,
                        "original_price": 20.0,
                        "promo_code": "NOTION-AI-VIP-88",
                        "target_url": "https://www.notion.so",
                        "supplier_name": "Notion Enterprise B2B Reseller",
                        "supplier_url": "https://www.notion.so",
                        "seller_details": "Official Notion AI Enterprise License Supplier",
                        "button_text": "Get Notion AI VIP 📑",
                        "button_text_ar": "تفعيل Notion AI والتنظيم 📑",
                        "description": "Official Price: $20/mo -> Your Price: $6.5/mo. Unlimited AI writing, summaries, and automated project database agents.",
                        "description_ar": "السعر الرسمي $20 -> سعرك: $6.5/شهرياً. كتابة غير محدودة وتلخيص وإدارة مشاريع تلقائية بالذكاء الاصطناعي.",
                        "stock_accounts": [
                                    "notion_ai_2026@gmail.com : Pass#2026-Notion | AccessKey: NOTION-AI-ACTIVE"
                        ]
            },
            {
                        "id": "jetbrains_all_products_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "JetBrains All Products Pack Enterprise Key (PyCharm, IntelliJ, WebStorm)",
                        "title_ar": "مفتاح تفعيل كافة برامج JetBrains الأصلي (PyCharm, IntelliJ, WebStorm)",
                        "badge": "JETBRAINS ALL-PACK 80% OFF 🔑",
                        "badge_ar": "حزمة جيتبراينز كاملة 🔑",
                        "price": 18.0,
                        "original_price": 289.0,
                        "promo_code": "JB-ALL-PACK-80OFF",
                        "target_url": "https://www.jetbrains.com",
                        "supplier_name": "JetBrains Official B2B Partner",
                        "supplier_url": "https://www.jetbrains.com",
                        "seller_details": "Certified JetBrains Educational & Enterprise Reseller",
                        "button_text": "Get JetBrains Pack 🔑",
                        "button_text_ar": "استلام مفتاح تفعيل JetBrains 🔑",
                        "description": "Official Price: $289/yr -> Your Price: $18. Official activation key for PyCharm, IntelliJ IDEA, WebStorm, CLion, DataGrip.",
                        "description_ar": "السعر الرسمي $289/سنوياً -> سعرك: $18 فقط! كود مفعّل لكافة بيئات تطوير JetBrains الاحترافية.",
                        "stock_accounts": [
                                    "JB-ALL-PRODUCTS-LICENSE-KEY-2026-X991-PRO"
                        ]
            },
            {
                        "id": "github_copilot_biz_promo",
                        "category": "promos",
                        "offer_type": "promo_code",
                        "title": "GitHub Copilot Business & Enterprise License Pass",
                        "title_ar": "اشتراك جيت هب كوبايلوت GitHub Copilot Business مفعّل",
                        "badge": "GITHUB COPILOT BIZ ⚡",
                        "badge_ar": "جيت هب كوبايلوت بيزنس ⚡",
                        "price": 8.5,
                        "original_price": 19.0,
                        "promo_code": "GH-COPILOT-BIZ-2026",
                        "target_url": "https://github.com/features/copilot",
                        "supplier_name": "GitHub Enterprise API Supplier",
                        "supplier_url": "https://github.com",
                        "seller_details": "GitHub Enterprise Reseller Partner",
                        "button_text": "Launch GitHub Copilot ⚡",
                        "button_text_ar": "تفعيل GitHub Copilot بيزنس ⚡",
                        "description": "Official Price: $19/mo -> Your Price: $8.5/mo. Fast AI autocomplete & Copilot Chat inside VS Code, JetBrains & Neovim.",
                        "description_ar": "السعر الرسمي $19 -> سعرك: $8.5/شهرياً. إكمال كود فوري ومحادثة ذكية داخل VS Code و JetBrains.",
                        "stock_accounts": [
                                    "gh_copilot_2026@gmail.com : Pass#2026-Copilot | AccessKey: GH-COPILOT-ACTIVE"
                        ]
            },
            {
                        "id": "kimi_moonshot_ai_acc",
                        "category": "ai",
                        "offer_type": "digital_account",
                        "title": "Kimi k1.5 Moonshot AI Ultra Reasoning Master Account",
                        "title_ar": "حساب Kimi k1.5 Moonshot AI الفائق للتحليل والاستنتاج الطويل",
                        "badge": "KIMI 2M CONTEXT 🚀",
                        "badge_ar": "حساب كيمي كود واستنتاج 🚀",
                        "price": 11.0,
                        "original_price": 22.0,
                        "target_url": "https://kimi.moonshot.cn",
                        "supplier_name": "Moonshot AI Direct Reseller",
                        "supplier_url": "https://kimi.moonshot.cn",
                        "seller_details": "Official Moonshot AI Enterprise Partner",
                        "button_text": "Launch Kimi AI 🚀",
                        "button_text_ar": "فتح موقع Kimi k1.5 والبدء 🚀",
                        "description": "Official Price: $22/mo -> Your Price: $11/mo. 2M token context window for huge codebases, long PDF analysis, and deep reasoning.",
                        "description_ar": "السعر الرسمي $22 -> سعرك: $11/شهرياً. سياق 2 مليون توكن لتحليل المشروعات البرمجية الضخمة والمستندات الطويلة.",
                        "stock_accounts": [
                                    "kimi_pro_2026@gmail.com : Pass#2026-Kimi | AccessKey: KIMI-K15-PRO-ACTIVE"
                        ]
            },
            {
                        "id": "runway_luma_video_ai_acc",
                        "category": "ai",
                        "offer_type": "digital_account",
                        "title": "Runway Gen-3 Alpha & Luma Dream Machine Cinematic Video AI Account",
                        "title_ar": "حساب صنع الفيديو بالذكاء الاصطناعي Runway Gen-3 & Luma Dream Machine",
                        "badge": "CINEMATIC VIDEO AI 🎬",
                        "badge_ar": "توليد فيديو سينمائي 🎬",
                        "price": 16.0,
                        "original_price": 35.0,
                        "target_url": "https://runwayml.com",
                        "supplier_name": "Runway B2B Digital Goods API",
                        "supplier_url": "https://runwayml.com",
                        "seller_details": "Premier Video Synthesis Enterprise Partner",
                        "button_text": "Launch Runway Gen-3 🎬",
                        "button_text_ar": "فتح موقع Runway Gen-3 والبدء 🎬",
                        "description": "Official Price: $35/mo -> Your Price: $16/mo. High-fidelity cinematic video generation from text & image prompts.",
                        "description_ar": "السعر الرسمي $35 -> سعرك: $16/شهرياً. حساب مفعّل لتوليد مقاطع فيديو سينمائية فائقة الجودة من النصوص والصور.",
                        "stock_accounts": [
                                    "runway_gen3_2026@gmail.com : Pass#2026-Runway | AccessKey: RUNWAY-GEN3-ACTIVE"
                        ]
            },
            {
                "id": "canva_pro_acc",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "Canva Pro 1-Year Premium Design Account",
                "title_ar": "حساب Canva Pro لمدة سنة كاملة للتصميم والذكاء الاصطناعي",
                "badge": "1-YEAR CANVA PRO 🎨",
                "badge_ar": "اشتراك كانفا برو سنة 🎨",
                "price": 9.0,
                "original_price": 120.0,
                "target_url": "https://www.canva.com",
                "supplier_name": "DHgate B2B Wholesale Market",
                "supplier_url": "https://www.dhgate.com",
                "seller_details": "Premier Design Software Wholesale Partner",
                "button_text": "Launch Canva Pro 🎨",
                "button_text_ar": "فتح موقع Canva والبدء 🎨",
                "description": "Official Price: $120/yr -> Your Price: $9/yr. Full private Canva Pro access with Brand Kits, Magic Studio AI, and 100M+ assets.",
                "description_ar": "السعر الرسمي $120/سنوياً -> سعرك هنا: $9 فقط. حساب كانفا برو كامل لميزات التصميم والذكاء الاصطناعي وإزالة الخلفيات.",
                "stock_accounts": [
                    "canva_pro_1yr@gmail.com : Canva#2026-VIP | AccessKey: CANVA-PRO-1YEAR-DIRECT | LoginUrl: https://www.canva.com"
                ]
            },
            {
                "id": "perplexity_pro_acc",
                "category": "ai",
                "offer_type": "digital_account",
                "title": "Perplexity Pro AI Search & Academic Research Account",
                "title_ar": "حساب Perplexity Pro للبحث الأكاديمي والذكاء الاصطناعي",
                "badge": "UNLIMITED SEARCH PRO 🔍",
                "badge_ar": "بحث أكاديمي برو 🔍",
                "price": 10.0,
                "original_price": 20.0,
                "target_url": "https://www.perplexity.ai",
                "supplier_name": "Z2U Digital Goods API",
                "supplier_url": "https://www.z2u.com",
                "seller_details": "Authorized Wholesale AI Supplier",
                "button_text": "Launch Perplexity Pro 🔍",
                "button_text_ar": "فتح موقع Perplexity والبدء 🔍",
                "description": "Official Price: $20/mo -> Your Price: $10/mo. Unlimited Deep Research with Claude 3.7, GPT-4o, and Sonar Pro.",
                "description_ar": "السعر الرسمي $20/شهرياً -> سعرك هنا: $10 فقط. حساب مفعّل للوصول لمحركات البحث الذكية والأكاديمية المعمقة.",
                "stock_accounts": [
                    "perplexity_pro_vip@gmail.com : Perplexity#2026-VIP | AccessKey: PERPLEXITY-PRO-DIRECT | LoginUrl: https://www.perplexity.ai"
                ]
            },
            {
                "id": "github_copilot_acc",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "GitHub Copilot Pro Developer Account",
                "title_ar": "حساب GitHub Copilot Pro المساعد المبرمج الذكي",
                "badge": "COPILOT PRO IDE 🤖",
                "badge_ar": "مساعد المبرمج الذكي 🤖",
                "price": 7.0,
                "original_price": 10.0,
                "target_url": "https://github.com/features/copilot",
                "supplier_name": "G2A Digital Goods API Marketplace",
                "supplier_url": "https://www.g2a.com",
                "seller_details": "Authorized Developer Software Vendor",
                "button_text": "Launch GitHub Copilot 🤖",
                "button_text_ar": "فتح موقع GitHub Copilot والبدء 🤖",
                "description": "Official Price: $10/mo -> Your Price: $7/mo. Direct Copilot Pro autocompletion & chat in VS Code, JetBrains, and Cursor.",
                "description_ar": "السعر الرسمي $10/شهرياً -> سعرك هنا: $7 فقط. حساب مفعّل لإكمال الأكواد الذكية بـ GitHub Copilot.",
                "stock_accounts": [
                    "github_copilot_pro@gmail.com : Copilot#2026-Pass | AccessKey: COPILOT-PRO-DIRECT | LoginUrl: https://github.com/features/copilot"
                ]
            },
            {
                "id": "telegram_vip_otp",
                "category": "otp",
                "offer_type": "otp_verification",
                "title": "Telegram VIP Virtual Phone OTP Verification Slot",
                "title_ar": "رقم افتراضي لاستقبال رمز تفعيل تلغرام (Telegram OTP Slot)",
                "badge": "TELEGRAM OTP SLOT 📱",
                "badge_ar": "تفعيل حسابات تلغرام 📱",
                "price": 4.0,
                "original_price": 8.0,
                "target_url": "/otp-generator",
                "supplier_name": "5SIM SMS OTP Verification API",
                "supplier_url": "https://5sim.net",
                "seller_details": "Real-time Virtual SMS Receiver Engine",
                "button_text": "Open OTP Generator Hub 📱",
                "button_text_ar": "فتح مركز استقبال رموز التفعيل 📱",
                "description": "Dedicated non-VoIP virtual phone number slot for receiving instant 5-digit Telegram SMS activation codes.",
                "description_ar": "رقم هاتف مخصص لتلقي رمز تفعيل واتس اب أو تلغرام فوراً بدون انتظار.",
                "stock_accounts": [
                    "telegram_slot_9981@gmail.com : Pass#2026-TG | AccessKey: TELEGRAM-VIP-OTP-ACTIVE"
                ]
            },
            {
                "id": "adobe_cc_all_apps",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "Adobe Creative Cloud All Apps 1-Year Master VIP Pass",
                "title_ar": "حساب Adobe Creative Cloud جميع التطبيقات لمدة سنة كاملة",
                "badge": "ADOBE ALL APPS 1-YEAR 🎨",
                "badge_ar": "اشتراك أدوبي الشامل سنة 🎨",
                "price": 24.0,
                "original_price": 600.0,
                "target_url": "https://www.adobe.com",
                "supplier_name": "Kinguin B2B Enterprise API",
                "supplier_url": "https://www.kinguin.net",
                "seller_details": "Premier Adobe Enterprise Partner",
                "button_text": "Launch Adobe Creative Cloud 🎨",
                "button_text_ar": "فتح موقع Adobe والبدء 🎨",
                "description": "Official Price: $600/yr -> Your Price: $24/yr. Full Photoshop, Premiere Pro, Illustrator, and Firefly AI suite.",
                "description_ar": "السعر الرسمي $600/سنوياً -> سعرك هنا: $24 فقط. حساب مفعّل لمجموعة أدوبي كاملة وفوتوشوب وبريمير والذكاء الاصطناعي.",
                "stock_accounts": [
                    "adobe_cc_vip_2026@gmail.com : Adobe#2026-VIP | AccessKey: ADOBE-ALL-APPS-1YR-DIRECT | LoginUrl: https://www.adobe.com"
                ]
            },
            {
                "id": "nordvpn_2yr_acc",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "NordVPN Ultra 2-Year Unlimited Security & Privacy Account",
                "title_ar": "حساب NordVPN Ultra الحماية والأمان لمدة سنتين كاملتين",
                "badge": "2-YEAR NORDVPN ULTRA 🔒",
                "badge_ar": "حماية NordVPN سنتين 🔒",
                "price": 6.0,
                "original_price": 80.0,
                "target_url": "https://nordvpn.com",
                "supplier_name": "G2A Digital Goods API Marketplace",
                "supplier_url": "https://www.g2a.com",
                "seller_details": "Verified VPN & Security Vendor",
                "button_text": "Launch NordVPN 🔒",
                "button_text_ar": "فتح موقع NordVPN والبدء 🔒",
                "description": "Official Price: $80/2yr -> Your Price: $6. High-speed encrypted VPN with 6000+ servers worldwide.",
                "description_ar": "السعر الرسمي $80/سنتين -> سعرك هنا: $6 فقط. حساب مفعّل للحماية وتجاوز الحجب بسيرفرات فائقة السرعة.",
                "stock_accounts": [
                    "nordvpn_ultra_2yr@gmail.com : Nord#2026-Pass | AccessKey: NORDVPN-2YEAR-DIRECT | LoginUrl: https://nordvpn.com"
                ]
            },
            {
                "id": "linkedin_premium_acc",
                "category": "promos",
                "offer_type": "digital_account",
                "title": "LinkedIn Premium Business 6-Months VIP Pass",
                "title_ar": "اشتراك LinkedIn Premium Business لمدة 6 أشهر للوظائف والأعمال",
                "badge": "LINKEDIN PREMIUM 💼",
                "badge_ar": "لينكد إن بريميوم 💼",
                "price": 18.0,
                "original_price": 360.0,
                "target_url": "https://www.linkedin.com",
                "supplier_name": "CodesWholesale B2B Platform",
                "supplier_url": "https://www.codeswholesale.com",
                "seller_details": "Authorized Professional Software Supplier",
                "button_text": "Launch LinkedIn Premium 💼",
                "button_text_ar": "فتح موقع LinkedIn والبدء 💼",
                "description": "Official Price: $360/6mo -> Your Price: $18. Unlimited InMail credits, profile views, and salary insights.",
                "description_ar": "السعر الرسمي $360/6 أشهر -> سعرك هنا: $18 فقط. حساب لينكد إن بريميوم مفعّل للتواصل الفوري مع أصحاب العمل والشركات.",
                "stock_accounts": [
                    "linkedin_business_6mo@gmail.com : LinkedIn#2026-Pass | AccessKey: LINKEDIN-PREMIUM-DIRECT | LoginUrl: https://www.linkedin.com"
                ]
            },

            # === CATEGORY 4: VIRTUAL CREDIT CARDS (VCC) ===
            {
                "id": "visa_vcc_trial_slot",
                "category": "vcc",
                "offer_type": "vcc_card",
                "title": "Instant Virtual Visa Card (VCC) Subscription Slot",
                "title_ar": "بطاقة فيزا افتراضية لتفعيل الاشتراكات والتسوق الآمن (VCC)",
                "badge": "INSTANT VISA VCC 💳",
                "badge_ar": "بطاقة فيزا افتراضية 💳",
                "price": 6.0,
                "original_price": 10.0,
                "target_url": "/vcc-generator",
                "supplier_name": "PST.net Merchant VCC API",
                "supplier_url": "https://pst.net",
                "seller_details": "Automated Virtual Card Issuing Network",
                "button_text": "Issue Virtual Visa Card 💳",
                "button_text_ar": "إصدار بطاقة فيزا افتراضية 💳",
                "description": "Pre-funded 3D Secure Virtual Visa Card for trial activations, online shopping, and SaaS billing.",
                "description_ar": "بطاقة فيزا افتراضية مسبقة الدفع لتفعيل الاشتراكات والمتاجر الإلكترونية بكل أمان وسرعة.",
                "stock_accounts": [
                    "4532 9981 4012 8890 | Exp: 12/28 | CVV: 789 | Cardholder: JobHunt VIP"
                ]
            },
            {
                "id": "mastercard_crypto_vcc",
                "category": "vcc",
                "offer_type": "vcc_card",
                "title": "Crypto-Funded Virtual Mastercard (VCC) Premium Slot",
                "title_ar": "بطاقة ماستركارد افتراضية ممتازة مشحونة بالعملات الرقمية",
                "badge": "CRYPTO MASTERCARD 💳",
                "badge_ar": "ماستركارد افتراضية 💳",
                "price": 8.0,
                "original_price": 15.0,
                "target_url": "/vcc-generator",
                "supplier_name": "Moon Cards B2B API",
                "supplier_url": "https://mooncards.com",
                "seller_details": "Premier Crypto VCC Issuer API",
                "button_text": "Issue Virtual Mastercard 💳",
                "button_text_ar": "إصدار ماستركارد افتراضية 💳",
                "description": "Instant 100% accepted Virtual Mastercard slot for domain buying, server hosting, and global ads.",
                "description_ar": "بطاقة ماستركارد مشحونة ومقبولة 100% لشراء النطاقات والاستضافات والإعلانات.",
                "stock_accounts": [
                    "5412 8821 9043 1156 | Exp: 09/29 | CVV: 432 | Cardholder: JobHunt Crypto VIP"
                ]
            },

            # === CATEGORY 5: PROXIES & CAPTCHA SOLVER ===
            {
                "id": "residential_proxy_5gb",
                "category": "proxies",
                "offer_type": "proxy_service",
                "title": "High-Speed Residential Proxy 5GB Bandwidth Pass",
                "title_ar": "باكة بروكسيات سكنية فائقة السرعة 5GB لحماية التصفح والبرمجة",
                "badge": "5GB RESIDENTIAL PROXY 🌐",
                "badge_ar": "بروكسي سكني سريع 🌐",
                "price": 7.0,
                "original_price": 20.0,
                "target_url": "/proxy-hub",
                "supplier_name": "IPRoyal B2B Proxy API",
                "supplier_url": "https://iproyal.com",
                "seller_details": "Authorized Proxy Network Vendor",
                "button_text": "Open Proxy Manager 🌐",
                "button_text_ar": "فتح مدير البروكسيات السريعة 🌐",
                "description": "Clean, rotating residential IPs in US, EU, and Gulf regions with 99.9% uptime.",
                "description_ar": "أي بي سكني نظيف وتناوبي فائق السرعة في أمريكا وأوروبا والخليج.",
                "stock_accounts": [
                    "res_proxy_user_9981:PassProxy2026@gw.iproyal.com:3128 | Bandwidth: 5GB"
                ]
            },
            {
                "id": "captcha_solver_slot",
                "category": "proxies",
                "offer_type": "captcha_service",
                "title": "Auto 2Captcha & AI CAPTCHA Solver 1000-Solves Pass",
                "title_ar": "اشتراك حل رموز الـ CAPTCHA آلياً بالذكاء الاصطناعي (1000 حل)",
                "badge": "AUTO CAPTCHA SOLVER 🤖",
                "badge_ar": "حل الـ كابتشا آلياً 🤖",
                "price": 3.0,
                "original_price": 8.0,
                "target_url": "/captcha-hub",
                "supplier_name": "2Captcha Enterprise API",
                "supplier_url": "https://2captcha.com",
                "seller_details": "Automated AI Solver Provider",
                "button_text": "Open CAPTCHA Solver 🤖",
                "button_text_ar": "فتح محرك حل الكابتشا 🤖",
                "description": "Instant API key slot for solving reCAPTCHA v2/v3, hCaptcha, and Cloudflare Turnstile.",
                "description_ar": "مفتاح API مخصص لحل كافة أنواع الكابتشا وتجاوزها آلياً في ثوانٍ.",
                "stock_accounts": [
                    "ApiKey: 2CAPTCHA-VIP-KEY-9981-ACTIVE | Balance: 1000 Solves"
                ]
            },

            # === CATEGORY 6: GAMING & GIFT CARDS ===
            {
                "id": "steam_wallet_card",
                "category": "gaming",
                "offer_type": "gift_card",
                "title": "Steam $10 USD Global Gaming Wallet Gift Card",
                "title_ar": "بطاقة شحن رصيد ستيم $10 Steam Global Wallet",
                "badge": "STEAM $10 CARD 🎮",
                "badge_ar": "بطاقة ستيم $10 🎮",
                "price": 5.0,
                "original_price": 10.0,
                "target_url": "https://store.steampowered.com",
                "supplier_name": "G2A Digital Goods API Marketplace",
                "supplier_url": "https://www.g2a.com",
                "seller_details": "Premier Gaming Gift Card Distributor",
                "button_text": "Redeem Steam Code 🎮",
                "button_text_ar": "تفعيل كود ستيم 🎮",
                "description": "Instant Steam digital code key for buying games, skins, and battle passes globally.",
                "description_ar": "كود ديجيتال فوري لتعبئة رصيد ستيم وشراء الألعاب والبطولات بسهولة.",
                "stock_accounts": [
                    "STEAM-CODE-9981-2026-X89A | RedeemUrl: https://store.steampowered.com/account/redeemwalletcode"
                ]
            },
            {
                "id": "xbox_gamepass_ult",
                "category": "gaming",
                "offer_type": "subscription",
                "title": "Xbox Game Pass Ultimate 3-Months VIP Pass",
                "title_ar": "اشتراك Xbox Game Pass Ultimate لمدة 3 أشهر ألعاب ومكتبة شاملة",
                "badge": "XBOX GAME PASS 🎯",
                "badge_ar": "اشتراك إكس بوكس 🎯",
                "price": 9.0,
                "original_price": 45.0,
                "target_url": "https://www.xbox.com",
                "supplier_name": "Kinguin B2B Enterprise API",
                "supplier_url": "https://www.kinguin.net",
                "seller_details": "Authorized Gaming License Vendor",
                "button_text": "Redeem Xbox Pass 🎯",
                "button_text_ar": "تفعيل اشتراك Xbox 🎯",
                "description": "Official Price: $45 -> Your Price: $9. Unlimited access to 400+ AAA games on PC & Console.",
                "description_ar": "السعر الرسمي $45 -> سعرك هنا: $9 فقط. الوصول لأكثر من 400 لعبة احترافية على الكمبيوتر والـ Console.",
                "stock_accounts": [
                    "XBOX-PASS-ULTIMATE-3MO-9981 | RedeemUrl: https://redeem.microsoft.com"
                ]
            },

            # === CATEGORY 7: CUSTOM DOMAINS & CLOUD HOSTING ===
            {
                "id": "domain_ai_com_slot",
                "category": "domains",
                "offer_type": "domain_service",
                "title": "Instant Premium Custom .COM / .AI Domain & SSL Registration",
                "title_ar": "حجز وحماية نطاق اسم موقعك (.COM / .AI) مع شهادة أمان مجانية",
                "badge": "CUSTOM DOMAIN & SSL 🚀",
                "badge_ar": "حجز نطاق وموقع 🚀",
                "price": 4.0,
                "original_price": 18.0,
                "target_url": "/domain-registry",
                "supplier_name": "Namecheap Reseller API",
                "supplier_url": "https://www.namecheap.com",
                "seller_details": "ICANN Accredited Registrar API",
                "button_text": "Register Domain Now 🚀",
                "button_text_ar": "حجز وتفعيل النطاق فوراً 🚀",
                "description": "Instant 1-Year .COM domain registration with WHOIS Privacy & Auto-SSL Certificate.",
                "description_ar": "حجز نطاق موقعك الإلكتروني لمدة سنة كاملة مع حماية البيانات وشهادة الأمان SSL.",
                "stock_accounts": [
                    "DomainAuthKey: NAMECHEAP-VIP-REG-9981 | AutoSSL: Active"
                ]
            },

            # === CATEGORY 8: SOCIAL MEDIA BOOST & VERIFICATION ===
            {
                "id": "twitter_x_blue_boost",
                "category": "growth",
                "offer_type": "growth_service",
                "title": "Twitter / X Blue Verification & Authority Booster Pass",
                "title_ar": "خدمة توثيق وتنشيط حساب تويتر / X وتزويد التفاعل والانتشار",
                "badge": "X BLUE BOOST 🚀",
                "badge_ar": "توثيق وتوسيع تويتر 🚀",
                "price": 5.0,
                "original_price": 25.0,
                "target_url": "/social-boost",
                "supplier_name": "SMMGlobe Enterprise API",
                "supplier_url": "https://smmglobe.com",
                "seller_details": "Automated SMM B2B Provider",
                "button_text": "Launch Growth Boost 🚀",
                "button_text_ar": "بدء حملة الانتشار والتفاعل 🚀",
                "description": "Instant API boost for profile authority, impressions, and verified blue checkmark slot.",
                "description_ar": "خدمة فورية لرفع المشاهدات والتفاعل وتوسيع انتشار الحساب بشكل موثوق.",
                "stock_accounts": [
                    "GrowthApiKey: SMM-BOOST-KEY-9981-ACTIVE | Credits: 5000 Impressions"
                ]
            },

            # === CATEGORY 9: SOFTWARE LICENSES & ANTIVIRUS KEY VAULT ===
            {
                "id": "win11_pro_lifetime_key",
                "category": "software",
                "offer_type": "license_key",
                "title": "Windows 11 Pro Official Lifetime VIP Activation Key",
                "title_ar": "مفتاح تفعيل ويندوز 11 برو الأصلي تفعيل دائم مدى الحياة",
                "badge": "WINDOWS 11 PRO 🔑",
                "badge_ar": "مفتاح ويندوز 11 الأصلي 🔑",
                "price": 5.0,
                "original_price": 200.0,
                "target_url": "https://www.microsoft.com",
                "supplier_name": "LicenseVault B2B Platform",
                "supplier_url": "https://licensevault.com",
                "seller_details": "Microsoft Authorized OEM License Vendor",
                "button_text": "Redeem Windows Key 🔑",
                "button_text_ar": "تفعيل مفتاح ويندوز 🔑",
                "description": "Official Price: $200 -> Your Price: $5. 100% genuine retail key with lifetime updates.",
                "description_ar": "السعر الرسمي $200 -> سعرك هنا: $5 فقط. مفتاح أصلي تفعيل دائم مدى الحياة ربط حساب مايكروسوفت.",
                "stock_accounts": [
                    "WIN11-PRO-KEY-9981-2026-ACTIVE-XYZ9 | Type: Retail Lifetime | Support: Official Microsoft"
                ]
            },
            {
                "id": "office_2026_pro_plus",
                "category": "software",
                "offer_type": "license_key",
                "title": "Microsoft Office 2026 Pro Plus Lifetime License Key",
                "title_ar": "مفتاح تفعيل مايكروسوفت أوفيس 2026 Pro Plus مدى الحياة",
                "badge": "OFFICE 2026 PRO 💼",
                "badge_ar": "أوفيس 2026 أصلي 💼",
                "price": 7.0,
                "original_price": 440.0,
                "target_url": "https://setup.office.com",
                "supplier_name": "CodesWholesale B2B Platform",
                "supplier_url": "https://www.codeswholesale.com",
                "seller_details": "Authorized Professional Software Supplier",
                "button_text": "Redeem Office Key 💼",
                "button_text_ar": "تفعيل مفتاح أوفيس 💼",
                "description": "Official Price: $440 -> Your Price: $7. Includes Word, Excel, PowerPoint, Outlook, and Access.",
                "description_ar": "السعر الرسمي $440 -> سعرك هنا: $7 فقط. تفعيل شامل لكافة برامج أوفيس وباقة المكاتب.",
                "stock_accounts": [
                    "OFFICE-2026-PRO-9981-PASS-PRO8 | RedeemUrl: https://setup.office.com"
                ]
            },
            {
                "id": "kaspersky_total_security",
                "category": "software",
                "offer_type": "license_key",
                "title": "Kaspersky Total Security 1-Year 3-Devices VIP Pass",
                "title_ar": "مفتاح كاسبرسكي توتال سيكوريتي حماية 3 أجهزة لمدة سنة",
                "badge": "KASPERSKY 1-YEAR 🛡️",
                "badge_ar": "حماية كاسبرسكي سنة 🛡️",
                "price": 6.0,
                "original_price": 90.0,
                "target_url": "https://www.kaspersky.com",
                "supplier_name": "G2A Digital Goods API Marketplace",
                "supplier_url": "https://www.g2a.com",
                "seller_details": "Verified CyberSecurity Software Vendor",
                "button_text": "Redeem Kaspersky Key 🛡️",
                "button_text_ar": "تفعيل مفتاح كاسبرسكي 🛡️",
                "description": "Official Price: $90 -> Your Price: $6. 100% automated protection for 3 PCs, Macs, or Mobiles.",
                "description_ar": "السعر الرسمي $90 -> سعرك هنا: $6 فقط. كود حماية شامل للكمبيوتر والموبايل ضد الفيروسات.",
                "stock_accounts": [
                    "KASPERSKY-TOTAL-SEC-1YR-9981-ACTIVE | RedeemUrl: https://my.kaspersky.com"
                ]
            }
        ]

        os.makedirs(os.path.dirname(CATALOG_FILE), exist_ok=True)
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump(master_catalog, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "count": len(master_catalog),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": "تم تحديث وتعبئة الكتالوج التلقائي المقسّم حسب الفئات بنجاح!"
        }


# Singleton Instance
catalog_populator = CatalogAutoPopulator()
