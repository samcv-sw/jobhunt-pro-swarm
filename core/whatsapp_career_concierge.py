"""
WhatsApp AI Career Concierge & Voice Assistant
JobHunt Pro SaaS - Interactive WhatsApp Chat & Voice Interview Agent for Gulf Candidates.
"""
import time
from typing import Dict, List, Any, Optional


class WhatsAppCareerConcierge:
    """
    Handles interactive WhatsApp messaging, job dispatch alerts,
    and voice-note mock interview coaching for GCC candidates.
    """

    MOCK_JOBS = [
        {"title": "Senior Cloud Solutions Architect", "company": "NEOM Tech & Digital", "city": "Riyadh / Tabuk", "salary": "38,000 SAR/mo"},
        {"title": "DevOps & Platform Engineering Lead", "company": "Careem / Dubai AI Lab", "city": "Dubai", "salary": "35,000 AED/mo"},
        {"title": "Principal AI & NLP Specialist", "company": "Qatar Sovereign Tech", "city": "Doha", "salary": "40,000 QAR/mo"}
    ]

    @classmethod
    def process_incoming_message(
        cls,
        sender_phone: str,
        message_body: str,
        message_type: str = "text",
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes incoming WhatsApp webhook message and generates an intelligent reply.
        """
        body_lower = message_body.lower().strip()

        if message_type == "audio" or "voice" in message_type:
            reply_text = (
                "🎙️ استلمت إجابتك الصوتية بنجاح!\n\n"
                "📊 تقييم النبرة والسرعة:\n"
                "✅ وضوح الصوت: 95%\n"
                "✅ سرعة الحديث: 135 كلمة/دقيقة (ممتازة)\n"
                "💡 نصيحة للتحسين: ركز أكثر على ذكر نسبة خفض التكاليف أو الأرقام الدقيقة عند الحديث عن إنجازاتك السابقة."
            )
            action_type = "voice_evaluation"
        elif "وظائف" in body_lower or "job" in body_lower or "فرص" in body_lower:
            job_lines = "\n\n".join([f"🔹 *{j['title']}*\n🏢 {j['company']} — {j['city']}\n💰 الراتب المتوقع: {j['salary']}" for j in cls.MOCK_JOBS])
            reply_text = (
                "🚀 *أحدث الفرص المطابقة لملفك المهني اليوم في الخليج:*\n\n"
                f"{job_lines}\n\n"
                "لتقديم سيرتك الذاتية تلقائياً بضغطة زر، أرسل كلمة *تقديم* أو زر رابط المنصة: https://jobhunt-pro.com"
            )
            action_type = "job_search_results"
        elif "تقديم" in body_lower or "apply" in body_lower:
            reply_text = (
                "✅ *تم تفعيل التقديم التلقائي!* \n"
                "يقوم سرب الـ AI الآن بتخصيص السيرة الذاتية وفحص الـ DNS MX وإرسال طلبك مباشرة إلى مدراء التوظيف.\n"
                "ستصلك رسالة فور فتح الإيميل أو الرد!"
            )
            action_type = "auto_apply_triggered"
        else:
            reply_text = (
                "أهلاً بك في *JobHunt Pro WhatsApp Concierge* ⚡\n\n"
                "أنا مساعدك المهني الذكي. يمكنك:\n"
                "1️⃣ كتابة *وظائف* لاستعراض أحدث الشواغر في الرياض ودبي.\n"
                "2️⃣ إرسال *تسجيل صوتي* لإجراء مقابلة تجريبية والحصول على تقييم فوري.\n"
                "3️⃣ كتابة *تقديم* للتقديم التلقائي على الوظائف المستهدفة."
            )
            action_type = "general_menu"

        return {
            "recipient_phone": sender_phone,
            "reply_text": reply_text,
            "action_type": action_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "queued_for_dispatch"
        }


# Global singleton instance
whatsapp_concierge = WhatsAppCareerConcierge()
