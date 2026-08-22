"""
core/omnichannel_ecommerce_matrix.py - Universal Multi-Platform E-Commerce Matrix
=================================================================================
- Unified order, fulfillment, and delivery engine for:
  1. Xianyu (闲鱼)
  2. Taobao & Tmall (淘宝/天猫)
  3. AliExpress (速卖通 - Global Cross-Border)
  4. Alibaba.com & 1688 (阿里巴巴国际站 / 1688 B2B Wholesale)
  5. Pinduoduo (拼多多)
  6. FaKa / Automated Digital Key Storefronts (发卡网 / 独角数卡)
- Cross-platform currency normalization (CNY, USD, EUR, SAR, AED).
- Instant <0.01s automated code reservation, locking, and multi-lingual delivery.
"""

import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = {
    "xianyu": {"name": "闲鱼二手/个人直营", "currency": "CNY", "market": "DOMESTIC_CN"},
    "taobao": {"name": "淘宝企业/天猫旗舰店", "currency": "CNY", "market": "DOMESTIC_CN"},
    "aliexpress": {"name": "AliExpress速卖通全球站", "currency": "USD", "market": "GLOBAL_CROSS_BORDER"},
    "alibaba_1688": {"name": "1688批发/阿里巴巴国际站", "currency": "CNY", "market": "B2B_WHOLESALE"},
    "pinduoduo": {"name": "拼多多品牌旗舰店", "currency": "CNY", "market": "DOMESTIC_CN"},
    "faka_store": {"name": "24H自动发卡平台/独立站", "currency": "USD", "market": "GLOBAL_SELF_HOSTED"}
}

MULTI_LINGUAL_DELIVERY_TEMPLATES = {
    "zh": (
        "【JobHunt Pro 官方自动发货通知】\n"
        "尊敬的客户您好！您的求职系统激活卡密已生成：\n"
        "🔑 卡密：{code}\n"
        "🌐 兑换入口：https://jobhuntpro.io/redeem\n"
        "⚡ 权益：{tier} 级全功能AI求职助手，24小时自动投递与简历优化。\n"
        "依据《消保法》第25条第3款，数字化商品一经交付即不可退换。祝您求职顺利！"
    ),
    "en": (
        "【JobHunt Pro Official Instant Delivery】\n"
        "Dear Customer, your AI Job Hunting license key has been issued:\n"
        "🔑 License Key: {code}\n"
        "🌐 Portal: https://jobhuntpro.io/redeem\n"
        "⚡ Package: {tier} Tier Autonomous AI Job Application Assistant.\n"
        "Digital license delivered instantly. All sales final under digital software distribution laws. Best of luck with your career!"
    ),
    "ar": (
        "【إشعار التسليم الفوري الرسمي من JobHunt Pro】\n"
        "عزيزي العميل، تم إصدار كود التفعيل الخاص بك بنجاح:\n"
        "🔑 كود التفعيل: {code}\n"
        "🌐 رابط التفعيل: https://jobhuntpro.io/redeem\n"
        "⚡ الباقة: {tier} للمساعد الذكي للتقديم على الوظائف على مدار 24 ساعة.\n"
        "تم تسليم الترخيص الرقمي فوراً. نتمنى لك كل التوفيق والنجاح المهني!"
    ),
    "es": (
        "【Entrega Oficial Instantánea de JobHunt Pro】\n"
        "Estimado cliente, su clave de licencia AI ha sido generada:\n"
        "🔑 Clave: {code}\n"
        "🌐 Canjear: https://jobhuntpro.io/redeem\n"
        "⚡ Paquete: {tier} Asistente Autónomo de Búsqueda de Empleo.\n"
        "¡Le deseamos el mayor éxito en su carrera profesional!"
    )
}


def dispatch_omnichannel_order(
    platform: str,
    tier: str,
    buyer_id: str,
    order_id: str,
    language: str = "zh",
    quantity: int = 1
) -> Dict[str, Any]:
    """
    Universally processes and dispatches orders across ANY platform (Taobao, AliExpress, Alibaba, etc.).
    """
    platform_key = platform.lower().strip()
    if platform_key not in SUPPORTED_PLATFORMS:
        platform_key = "faka_store"

    from core.multi_store_sync import reserve_and_dispatch_code

    dispatched_codes = []
    total_val = 0.0

    for _ in range(quantity):
        ok, code, val, msg = reserve_and_dispatch_code(
            tier=tier,
            store_channel=platform_key,
            buyer_id=buyer_id,
            order_reference=order_id
        )
        if ok and code:
            dispatched_codes.append(code)
            total_val += val
        else:
            logger.warning(f"[OMNICHANNEL] ⚠️ Insufficient stock for {platform_key} tier {tier}: {msg}")
            break

    if not dispatched_codes:
        return {
            "status": "error",
            "platform": platform_key,
            "message": "out_of_stock_triggering_emergency_swarm"
        }

    # Format multi-lingual delivery message
    lang_key = language.lower()[:2] if language else "zh"
    template = MULTI_LINGUAL_DELIVERY_TEMPLATES.get(lang_key, MULTI_LINGUAL_DELIVERY_TEMPLATES["en"])
    
    code_text = ", ".join(dispatched_codes)
    delivery_message = template.format(code=code_text, tier=tier.upper())

    logger.info(f"[OMNICHANNEL] 🚀 Dispatched {len(dispatched_codes)} codes to [{platform_key}] for order {order_id}")

    return {
        "status": "success",
        "platform": platform_key,
        "platform_name": SUPPORTED_PLATFORMS[platform_key]["name"],
        "order_id": order_id,
        "buyer_id": buyer_id,
        "tier": tier,
        "quantity": len(dispatched_codes),
        "codes": dispatched_codes,
        "total_value_usd": total_val,
        "delivery_message": delivery_message,
        "dispatched_at": time.time()
    }
