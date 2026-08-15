"""
AI Video Elevator Pitch & Script Generator
JobHunt Pro SaaS - Produces high-converting 45-second video resume scripts with scene cues and overlays.
"""
from typing import Dict, List, Any, Optional


class AiVideoPitchEngine:
    """
    Generates cinematic, timed video elevator pitch scripts optimized for recruiter attention.
    """

    @classmethod
    def generate_pitch_package(
        cls,
        candidate_name: str,
        current_title: str,
        key_achievement: str = "Scaled microservices to 100k req/sec while cutting cloud bill by 35%",
        target_company_type: str = "GCC Sovereign / Scale-up Enterprise",
        duration_seconds: int = 45
    ) -> Dict[str, Any]:
        """
        Generates 4-scene video script with pacing, camera directions, and on-screen graphics (GOG).
        """
        scenes = [
            {
                "scene_number": 1,
                "time_range": "0:00 – 0:08",
                "scene_name": "The Powerful Hook",
                "camera_shot": "Medium Close-up, Direct Eye Contact, Confident Posture",
                "spoken_script_en": f"Hi, I'm {candidate_name}. As a {current_title}, I specialize in building fault-tolerant systems that drive exponential scale.",
                "spoken_script_ar": f"مرحباً، أنا {candidate_name}. بصفتي {current_title}، أركز على بناء بنى تحتية سحابية عالية الاعتمادية تحقق نمواً استثنائياً للشركات.",
                "on_screen_graphic": f"{candidate_name} | {current_title}",
                "director_note": "Deliver with strong vocal energy and warm smile."
            },
            {
                "scene_number": 2,
                "time_range": "0:08 – 0:25",
                "scene_name": "Quantifiable Proof of Impact",
                "camera_shot": "Slide zoom-in, side graphic overlay showing key metrics",
                "spoken_script_en": f"In my recent role, I {key_achievement}. I don't just write code; I design systems that translate engineering into direct business profit.",
                "spoken_script_ar": f"في مسيرتي الأخيرة، قمت بـ {key_achievement}. دوري لا يقتصر على كتابة الكود فقط، بل تحويل الهندسة البرمجية إلى عوائد مالية واستقرار تشغيلي مباشر.",
                "on_screen_graphic": "📊 Metric Highlight: 99.99% Uptime | -35% Cost Overhead",
                "director_note": "Pace steadily. Emphasize the numbers clearly."
            },
            {
                "scene_number": 3,
                "time_range": "0:25 – 0:38",
                "scene_name": "Strategic Alignment & Vision",
                "camera_shot": "Slight angle shift, engaging hand gestures",
                "spoken_script_en": f"I'm now looking to bring this track record to leading teams in {target_company_type}, solving complex challenges in high-growth environments.",
                "spoken_script_ar": f"أتطلع اليوم لتسخير هذه الخبرات لقيادة مشاريع نوعية ضمن بيئات العمل الرائدة، والمساهمة الفعالة في تحقيق مستهدفات التحول الرقمي.",
                "on_screen_graphic": f"🎯 Target: {target_company_type}",
                "director_note": "Show vision and strategic leadership tone."
            },
            {
                "scene_number": 4,
                "time_range": "0:38 – 0:45",
                "scene_name": "Frictionless Call to Action",
                "camera_shot": "Direct to camera, closing smile",
                "spoken_script_en": "I'd love to connect and share how we can accelerate your technical roadmap. Let's start the conversation.",
                "spoken_script_ar": "يسعدني التواصل معكم لاستعراض كيف يمكننا تسريع خارطة الطريق التقنية لفريقكم. شكراً لوقتكم.",
                "on_screen_graphic": "🔗 Connect via LinkedIn / WhatsApp",
                "director_note": "Warm, welcoming closing invitation."
            }
        ]

        full_en = " ".join([s["spoken_script_en"] for s in scenes])
        full_ar = " ".join([s["spoken_script_ar"] for s in scenes])

        return {
            "candidate_name": candidate_name,
            "target_title": current_title,
            "target_duration_seconds": duration_seconds,
            "total_words_en": len(full_en.split()),
            "total_words_ar": len(full_ar.split()),
            "estimated_pacing_wpm": 135,
            "scenes": scenes,
            "full_script_en": full_en,
            "full_script_ar": full_ar,
            "shareable_video_card_url": f"https://jobhunt-pro.com/v/{candidate_name.lower().replace(' ', '-')}"
        }


# Global singleton instance
ai_video_pitch_engine = AiVideoPitchEngine()
