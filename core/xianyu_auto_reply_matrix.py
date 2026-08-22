"""
core/xianyu_auto_reply_matrix.py - Xianyu / Taobao AI Auto-Reply Matrix (闲鱼/淘宝智能全自动客服系统)
=============================================================================================
- High-conversion, native Mandarin Chinese automated customer service reply engine.
- Instant (<0.01s) keyword & intent matching for pre-sale inquiries, delivery, and troubleshooting.
- Perfectly maintains the enterprise cloud automated provider persona with 0 foreign disclosure.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Native Mandarin Chinese Conversational Repertoire
AUTO_REPLIES: Dict[str, Dict[str, any]] = {
    "is_instant": {
        "keywords": ["在吗", "秒发", "自动发货", "多久发货", "现在能发吗", "立刻", "什么时候发", "在不", "有人吗"],
        "reply": (
            "亲您好！【24小时全自动秒发】拍下后系统将在 3 秒内自动发送激活卡密与专属兑换链接到聊天窗口，"
            "无需人工值守，随时拍下随时可用！✨"
        )
    },
    "how_to_use": {
        "keywords": ["怎么用", "怎么使用", "如何使用", "教程", "兑换方法", "怎么激活", "如何激活", "怎么充值", "在哪里充值", "使用说明", "入口", "网址"],
        "reply": (
            "【使用极简教程】\n"
            "1. 复制聊天窗口中收到的卡密（格式如：XY-PRO-XXXX-XXXX）。\n"
            "2. 打开官方兑换页面，输入卡密并绑定您的邮箱/账号即可完成充值。\n"
            "3. 充值成功后，AI 智能求职投递额度实时入账，立即开启 24 小时全自动求职！🚀"
        )
    },
    "what_is_included": {
        "keywords": ["包含什么", "有什么功能", "额度", "包含哪些", "pro", "enterprise", "功能介绍", "能投多少"],
        "reply": (
            "【JobHunt Pro 智能求职系统核心权益】\n"
            "🔹 AI 简历高分深度优化（中英双语 / 匹配 ATS 算法）\n"
            "🔹 智能企业直聘邮箱精准挖掘（覆盖海内外名企/外企/大厂）\n"
            "🔹 24小时全自动 AI 投递助手与智能跟进\n"
            "🔹 投递状态与数据看板实时回传，大幅提升面试邀请率！💼"
        )
    },
    "refund_policy": {
        "keywords": ["退款", "能退吗", "七天", "退货", "保证", "不合适"],
        "reply": (
            "亲，本商品为数字化虚拟软件额度与激活卡密，拍下后由云端服务器实时生成派发。"
            "依据《中华人民共和国消费者权益保护法》第二十五条第三款规定，数字化商品一经交付或激活即不适用七日无理由退货。"
            "系统保证卡密 100% 正品官方有效，请放心使用！🤝"
        )
    },
    "troubleshoot_code": {
        "keywords": ["无效", "错误", "用不了", "没反应", "报错", "格式不对", "不能充值"],
        "reply": (
            "【卡密排错小贴士】\n"
            "1. 请核对卡密前后是否有空格或换行符，建议直接点击【复制卡密】。\n"
            "2. 请确认网络环境稳定，避免在开启特殊代理时频繁切换节点。\n"
            "3. 若仍有问题，请将报错截图发在聊天框，云端监控系统会自动为您核验处理！🛠️"
        )
    },
    "device_compat": {
        "keywords": ["手机能用吗", "电脑", "ipad", "苹果", "安卓", "mac", "windows", "支持什么设备"],
        "reply": (
            "亲，JobHunt Pro 为全平台自适应 Web 架构，支持【手机 / 电脑 / iPad / Mac / Windows】全设备网页端直接登录使用，无需繁琐下载安装，随开随用！📱💻"
        )
    },
    "default_greeting": {
        "keywords": [],
        "reply": (
            "您好！JobHunt Pro 云端智能客服为您服务。本店已接入全自动秒发系统，"
            "看中规格直接拍下即可秒提卡密，24小时在线支持！祝您求职顺利，拿到心仪Offer！🌟"
        )
    }
}


def match_xianyu_auto_reply(message: str) -> Tuple[str, str]:
    """
    Analyzes buyer message and returns (matched_category, reply_text).
    """
    if not message:
        return "default_greeting", AUTO_REPLIES["default_greeting"]["reply"]

    clean_msg = message.strip().lower()
    for cat_name, cat_data in AUTO_REPLIES.items():
        if cat_name == "default_greeting":
            continue
        for kw in cat_data["keywords"]:
            if kw.lower() in clean_msg:
                return cat_name, cat_data["reply"]

    return "default_greeting", AUTO_REPLIES["default_greeting"]["reply"]
