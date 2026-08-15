"""
Multimodal Vision & Body Language Interview Analyzer
JobHunt Pro SaaS - Real-Time AI Computer Vision & Vocal Prosody Engine
"""
import math
import time
from typing import Dict, List, Any, Optional


class MultimodalVisionInterviewAnalyzer:
    """
    Analyzes real-time video frames and audio telemetry during candidate mock interviews.
    Computes Eye-Contact Ratio, Posture Stability, Smile/Warmth Index, Speech Cadence,
    Filler Word Frequency, and overall Confidence Index.
    """

    FILLER_WORDS_EN = ["um", "uh", "like", "you know", "basically", "actually", "literally", "sort of", "kind of"]
    FILLER_WORDS_AR = ["يعني", "أصلاً", "تقريباً", "في الحقيقة", "نوعاً ما", "بشكل عام", "يعني زي ما تقول"]

    @classmethod
    def analyze_frame_telemetry(
        cls,
        face_detected: bool,
        gaze_pitch: float,      # Angle up/down in degrees
        gaze_yaw: float,        # Angle left/right in degrees
        smile_intensity: float, # 0.0 to 1.0
        head_tilt: float,       # Tilt angle in degrees
        shoulder_level_delta: float, # Difference in shoulder height
        lighting_lux: float = 120.0
    ) -> Dict[str, Any]:
        """
        Evaluates a single video frame telemetry payload.
        """
        if not face_detected:
            return {
                "face_detected": False,
                "eye_contact": False,
                "confidence_score": 20.0,
                "feedback": "Face not clearly visible in camera frame. Adjust camera angle.",
                "feedback_ar": "الوجه غير ظاهر بوضوح في الكاميرا. يرجى تعديل زاوية الإضاءة والكاميرا."
            }

        # Eye contact threshold: within ±15 degrees pitch and yaw
        eye_contact = abs(gaze_pitch) <= 15.0 and abs(gaze_yaw) <= 15.0
        gaze_offset = math.sqrt(gaze_pitch**2 + gaze_yaw**2)

        # Posture score (head tilt <= 10 deg, shoulder level delta <= 0.05)
        posture_score = 100.0 - min(100.0, (abs(head_tilt) * 2.5 + shoulder_level_delta * 200.0))
        posture_score = max(30.0, posture_score)

        # Warmth & expression score
        warmth_score = min(100.0, smile_intensity * 80.0 + (30.0 if eye_contact else 10.0))

        # Overall Frame Score
        confidence = (
            (40.0 if eye_contact else max(10.0, 40.0 - gaze_offset * 1.5)) +
            (posture_score * 0.35) +
            (warmth_score * 0.25)
        )
        confidence = round(min(100.0, max(0.0, confidence)), 1)

        feedback_en = []
        feedback_ar = []

        if not eye_contact:
            feedback_en.append("Maintain direct eye contact with the camera lens.")
            feedback_ar.append("حافظ على التواصل البصري المباشر مع عدسة الكاميرا.")
        if posture_score < 70.0:
            feedback_en.append("Straighten your posture and keep shoulders relaxed and level.")
            feedback_ar.append("اجلس بوضعية مستقيمة واجعل الكتفين في مستوى متناسق ومريح.")
        if smile_intensity < 0.15:
            feedback_en.append("Use natural facial warmth and subtle nods during key points.")
            feedback_ar.append("ابتسم بنعومة واستخدم تعابير وجه ودية تظهر التفاعل والحماس.")

        return {
            "face_detected": True,
            "eye_contact": eye_contact,
            "gaze_offset_degrees": round(gaze_offset, 2),
            "posture_score": round(posture_score, 1),
            "warmth_score": round(warmth_score, 1),
            "lighting_optimal": lighting_lux >= 80.0,
            "confidence_score": confidence,
            "tips_en": feedback_en or ["Excellent presence and eye contact!"],
            "tips_ar": feedback_ar or ["حضور ممتاز وتواصل بصري رائع وموثوق!"]
        }

    @classmethod
    def evaluate_speech_prosody(
        cls,
        transcript_text: str,
        duration_seconds: float,
        pitch_variance_hz: float = 25.0
    ) -> Dict[str, Any]:
        """
        Evaluates spoken answer cadence, words per minute (WPM), and filler words.
        Ideal WPM for professional English/Arabic is 120-160 WPM.
        """
        words = transcript_text.strip().split()
        word_count = len(words)
        duration_min = max(0.1, duration_seconds / 60.0)
        wpm = round(word_count / duration_min, 1)

        # Detect filler words
        text_lower = transcript_text.lower()
        fillers_detected_en = {f: text_lower.count(f) for f in cls.FILLER_WORDS_EN if f in text_lower}
        fillers_detected_ar = {f: text_lower.count(f) for f in cls.FILLER_WORDS_AR if f in text_lower}
        total_fillers = sum(fillers_detected_en.values()) + sum(fillers_detected_ar.values())

        filler_ratio = total_fillers / max(1, word_count)

        # Pace Score (optimal 130-155 WPM)
        if 120 <= wpm <= 165:
            pace_rating = "Optimal Pace"
            pace_score = 95.0
        elif wpm < 120:
            pace_rating = "Slightly Slow"
            pace_score = max(50.0, 95.0 - (120 - wpm) * 0.8)
        else:
            pace_rating = "Rushed / Fast"
            pace_score = max(40.0, 95.0 - (wpm - 165) * 1.2)

        # Clarity Score penalizing excessive filler words
        clarity_score = round(max(30.0, 100.0 - (filler_ratio * 300.0)), 1)
        composite_speech_score = round((pace_score * 0.5) + (clarity_score * 0.5), 1)

        recommendations = []
        recommendations_ar = []

        if filler_ratio > 0.04:
            recommendations.append(f"Reduce filler words ({total_fillers} detected). Embrace intentional pauses.")
            recommendations_ar.append(f"قلل من الكلمات الحشوية (تم رصد {total_fillers}). استخدم الصمت المؤقت للتفكير بدلاً منها.")
        if wpm > 165:
            recommendations.append("Slow down slightly to emphasize key quantifiable achievements.")
            recommendations_ar.append("تمهل قليلاً في الحديث لإبراز الأرقام والإنجازات الجوهرية بوضوح.")
        elif wpm < 115:
            recommendations.append("Increase speech momentum and energy to convey proactive leadership.")
            recommendations_ar.append("ارفع وتيرة الحماس والطاقة في الحديث لإظهار الثقة والمبادرة.")

        return {
            "word_count": word_count,
            "duration_seconds": round(duration_seconds, 1),
            "words_per_minute": wpm,
            "pace_rating": pace_rating,
            "filler_words_count": total_fillers,
            "filler_words_breakdown": {**fillers_detected_en, **fillers_detected_ar},
            "clarity_score": clarity_score,
            "composite_speech_score": composite_speech_score,
            "recommendations_en": recommendations or ["Pacing and clarity are crystal clear!"],
            "recommendations_ar": recommendations_ar or ["النبرة وسرعة الحديث واضحة وممتازة جداً!"]
        }

    @classmethod
    def generate_full_session_scorecard(
        cls,
        candidate_name: str,
        target_role: str,
        frame_telemetries: List[Dict[str, Any]],
        speech_eval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combines vision and audio telemetry into an executive candidate performance scorecard.
        """
        if not frame_telemetries:
            avg_vision_score = 80.0
            eye_contact_percentage = 85.0
            posture_avg = 88.0
        else:
            avg_vision_score = sum(f.get("confidence_score", 70.0) for f in frame_telemetries) / len(frame_telemetries)
            eye_contact_percentage = (sum(1 for f in frame_telemetries if f.get("eye_contact")) / len(frame_telemetries)) * 100.0
            posture_avg = sum(f.get("posture_score", 75.0) for f in frame_telemetries) / len(frame_telemetries)

        speech_score = speech_eval.get("composite_speech_score", 85.0)
        overall_index = round((avg_vision_score * 0.45) + (speech_score * 0.55), 1)

        if overall_index >= 90.0:
            readiness_tier = "Top 1% Elite Candidate (Executive Ready)"
            readiness_tier_ar = "مرشح استثنائي في أعلى 1% (جاهز للمناصب التنفيذية)"
            badge_color = "#00d4aa"
        elif overall_index >= 75.0:
            readiness_tier = "Strong Contender (Interview Qualified)"
            readiness_tier_ar = "مرشح قوي ومؤهل لاجتياز المقابلات بجدارة"
            badge_color = "#3b82f6"
        else:
            readiness_tier = "Needs Polish & Coaching"
            readiness_tier_ar = "يحتاج إلى تدريب إضافي وتطوير الأداء"
            badge_color = "#f0c040"

        return {
            "candidate_name": candidate_name,
            "target_role": target_role,
            "session_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "overall_interview_index": overall_index,
            "readiness_tier": readiness_tier,
            "readiness_tier_ar": readiness_tier_ar,
            "badge_color": badge_color,
            "vision_breakdown": {
                "eye_contact_percentage": round(eye_contact_percentage, 1),
                "posture_average": round(posture_avg, 1),
                "avg_visual_confidence": round(avg_vision_score, 1)
            },
            "speech_breakdown": speech_eval,
            "hiring_probability_boost": f"+{min(85, int(overall_index * 0.88))}%"
        }


# Global singleton instance
multimodal_vision_analyzer = MultimodalVisionInterviewAnalyzer()
