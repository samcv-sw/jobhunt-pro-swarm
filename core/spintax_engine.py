"""
Dynamic AI Spintax Engine
Transforms email outreach and cover letter templates into thousands of
semantically diverse variants to prevent spam-filter pattern recognition.
"""

import re
import random
from typing import Dict, Any, List, Optional


class SpintaxEngine:
    @classmethod
    def expand(cls, text: Optional[str]) -> str:
        """Alias for spin method to expand spintax strings."""
        return cls.spin(text)

    @staticmethod
    def spin(text: Optional[str]) -> str:
        """
        Recursively resolves spintax patterns like:
        {Hi|Hello|Dear} {Mr.|Ms.|Dr.} {Name}, {I am thrilled|I would love} to apply...
        """
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)

        pattern = re.compile(r'\{([^{}]+)\}')
        
        while True:
            match = pattern.search(text)
            if not match:
                break
            options = match.group(1).split('|')
            chosen = random.choice(options).strip()
            text = text[:match.start()] + chosen + text[match.end():]
            
        return text

    @staticmethod
    def generate_personalized_pitch(candidate_name: str, target_role: str, company: str, contact_name: str = "") -> str:
        """
        Produces a hyper-personalized, high-converting outreach message using rich spintax.
        """
        salutation = f"{{Dear|Hi|Hello}} {contact_name}," if contact_name else "{Dear Hiring Team|Hello Team|Greetings},"
        
        template = f"""{salutation}

{{I came across the|I noticed the recent|I was excited to see the}} {target_role} {{opening|opportunity|position}} at {company} and {{wanted to reach out directly|felt compelled to share my qualifications|would love to introduce myself}}.

{{With deep hands-on expertise in|Having a solid track record in|Specializing in}} modern cloud architecture, scalable backends, and AI automation, {{I have consistently delivered|I have driven significant business impact and|I bring proven experience in}} high-throughput systems.

{{I have attached my tailored resume for your review|Please find my CV attached with specific references to your tech stack|My updated resume is attached for your consideration}}. {{I would welcome the chance to discuss how I can contribute to {company}'s ongoing success.|I look forward to discussing how my background aligns with your upcoming goals.|Would you be open for a brief 10-minute introductory conversation this week?}}

{{Best regards|Sincerely|Warm regards|Kind regards}},
{candidate_name}
"""
        return SpintaxEngine.spin(template)

    @staticmethod
    def generate_psychographic_pitch(
        candidate_name: str,
        target_role: str,
        company: str,
        persona: str = "enterprise_executive",
        contact_name: str = "",
        language: str = "en"
    ) -> str:
        """
        Generates psychographic-aligned pitch permutations tailored to specific corporate archetypes:
        - enterprise_executive: High governance, ROI, architectural stability
        - startup_agile: Fast execution, speed to market, ownership
        - gcc_visionary: Vision 2030 alignment, regional expansion, prestige
        - fintech_security: Zero-trust, latency, compliance, transactional throughput
        """
        if language.lower() in ["ar", "arabic"]:
            if persona == "gcc_visionary":
                template = f"""{{سعادة الأستاذ|الأستاذ الفاضل|فريق القيادة الموقر}} {contact_name if contact_name else ''}،

{{تابعت باعتزاز كبير|أتابع باهتمام بالغ|يسعدني مواكبة}} {{مسيرة نمو|المشاريع النوعية لشركة|التوسع الاستراتيجي لـ}} {company} ودوركم الريادي في دعم مسيرة التحول الرقمي.

بصفتي {{متخصصاً في|خبيراً في مجال|مهندساً متمرساً في}} {target_role}، {{نجحت في قيادة وبناء|أمتلك سجلاً حافلاً في تطوير|ساهمت في تحسين كفاءة}} الأنظمة السحابية المتقدمة وحلول الذكاء الاصطناعي ذات الأداء الفائق.

{{يسرني إرفاق سيرتي الذاتية للاطلاع|تجدون برفقه ملف خبراتي وإنجازاتي|أضع بين أيديكم ملخصاً لأبرز المشاريع التي أنجزتها}}. {{ويشرفني عقد لقاء قصير لمناقشة آفاق التعاون وخدمة تطلعاتكم المستقبلية.|أتطلع لفرصة حوار مثمر لاستعراض سبل الإسهام في تحقيق أهدافكم.|هل يناسبكم اتصال تعريفي مقتضب هذا الأسبوع؟}}

{{مع خالص التقدير والاحترام|وتفضلوا بقبول فائق الاحترام والتقدير|دمتم بخير وعافية}}،
{candidate_name}"""
            else:
                template = f"""{{عزيزي|مرحباً|تحية طيبة}} {contact_name if contact_name else ''}،

{{أكتب إليكم بخصوص دور|لفتت انتباهي فرصة|أود التقدم لشاغر}} {target_role} لدى {company}.

{{أمتلك خبرة عملية مكثفة في|تخصصت على مدار سنوات في|بفضل خلفيتي التقنية في}} بناء الأنظمة القابلة للتوسع وأتمتة العمليات، {{حيث حققت نتائج ملموسة في|وقد تمكنت من رفع الكفاءة و|مع التركيز الدائم على}} سرعة التنفيذ وجودة المخرجات.

{{مرفق لكم سيرتي الذاتية المفصلة|يسعدني مشاركة السيرة الذاتية معكم|أرفق لكم ملخص مؤهلاتي}}. {{أتطلع لمكالمة سريعة للحديث حول القيمة التي يمكنني إضافتها لفريقكم.|هل أنتم متاحون لنقاش سريع ومثمر؟}}

{{تحياتي الخالصة|مع أطيب التحيات|دمتم بخير}}،
{candidate_name}"""
            return SpintaxEngine.spin(template)

        # English Psychographic Profiles
        if persona == "startup_agile":
            template = f"""{{Hey|Hi}} {contact_name if contact_name else 'team'},

{{Saw what you guys are building at|Been tracking {company}'s impressive growth curve|Love the product momentum at}} {company} and {{wanted to reach out directly regarding the|would love to jump in as your next|felt my background is a direct fit for the}} {target_role} {{role|opening|challenge}}.

{{I specialize in shipping fast, cutting tech debt, and owning backend systems end-to-end.|I thrive in high-velocity environments where shipping reliable features daily is the norm.|I bring hands-on experience scaling distributed microservices under zero-downtime constraints.}}

{{CV is attached with direct links to recent builds.|My resume with project metrics is attached.|Attached is my resume covering recent scalable deployments.}} {{Open for a quick 10-minute sync this week?|Let me know if you're free for a quick chat Thursday!|Would love to trade notes on your current engineering roadmap.}}

{{Cheers|Best|Best regards}},
{candidate_name}"""
        elif persona == "fintech_security":
            template = f"""{{Dear|Hello}} {contact_name if contact_name else 'Hiring Team'},

{{I am writing to express my strong interest in the|I would like to submit my candidacy for the|I am reaching out regarding the}} {target_role} {{position|opportunity}} at {company}.

{{With a rigorous focus on zero-trust architectures, low-latency transaction processing, and regulatory compliance|Having engineered high-throughput, fault-tolerant financial pipelines with sub-millisecond SLAs|Specializing in resilient cloud infrastructures and enterprise data integrity}}, {{I ensure mission-critical systems operate with 99.999% availability.|I have repeatedly delivered robust, scalable services under strict audit benchmarks.}}

{{Please find my detailed resume attached for your evaluation.|My comprehensive CV and credentials are attached.|I have attached my resume detailing relevant production achievements.}} {{I would welcome an introductory discussion regarding how my skill set aligns with {company}'s architectural standards.|Are you available for a brief introductory call this week?}}

{{Sincerely|Respectfully|Kind regards}},
{candidate_name}"""
        else: # enterprise_executive
            template = f"""{{Dear|Hello}} {contact_name if contact_name else 'Hiring Committee'},

{{I am reaching out to share my qualifications for the|I wish to formally present my profile for the|I am writing regarding the}} {target_role} {{engagement|mandate|role}} with {company}.

{{Throughout my career, I have specialized in architecting scalable platforms, streamlining delivery lifecycles, and aligning engineering execution with strategic corporate objectives.|I bring a proven record of driving operational efficiency, leading high-performing technical squads, and modernizing cloud ecosystems.|My background centers on architecting resilient, multi-region distributed backends with strict cost governance.}}

{{My CV is attached for your consideration.|Please review my attached resume summarizing quantitative impact across past mandates.|I have enclosed my professional dossier for your review.}} {{I would welcome the opportunity to discuss how my expertise can accelerate {company}'s strategic initiatives.|Would you be open to an introductory conversation at your earliest convenience?}}

{{Sincerely|Best regards|Warm regards}},
{candidate_name}"""

        return SpintaxEngine.spin(template)


def expand_spintax(text: Optional[str], seed: Optional[int] = None) -> str:
    """Expand a spintax string with optional deterministic seed."""
    if text is None:
        return ""
    if seed is not None:
        random.seed(seed)
    return SpintaxEngine.spin(text)


def calculate_jaccard_distance(str1: str, str2: str) -> float:
    """Calculate the Jaccard distance (1 - Jaccard similarity) between two texts."""
    if not str1 and not str2:
        return 0.0
    set1 = set(re.findall(r'\w+', (str1 or "").lower()))
    set2 = set(re.findall(r'\w+', (str2 or "").lower()))
    if not set1 and not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    similarity = intersection / union if union > 0 else 0.0
    return round(1.0 - similarity, 4)


def generate_unique_variations(
    template: str,
    count: int = 3,
    min_jaccard: float = 0.1,
    max_attempts: int = 20,
    seed: Optional[int] = None,
) -> List[str]:
    """Generate a list of unique spintax variations that meet minimum Jaccard diversity."""
    if seed is not None:
        random.seed(seed)

    variations = []
    attempts = 0
    while len(variations) < count and attempts < max_attempts:
        attempts += 1
        candidate = expand_spintax(template)
        if not variations:
            variations.append(candidate)
            continue
        
        # Check uniqueness against existing variations
        is_diverse = all(calculate_jaccard_distance(candidate, existing) >= min_jaccard for existing in variations)
        if is_diverse and candidate not in variations:
            variations.append(candidate)
            
    if not variations:
        variations.append(expand_spintax(template))
    return variations


def generate_ultra_distinct_batch(
    template: str,
    batch_size: int = 5,
    min_jaccard_distance: float = 0.30,
    seed: Optional[int] = None,
    max_attempts: int = 100,
) -> Dict[str, Any]:
    """
    Generates a batch of distinct, high-entropy variations using Jaccard distance guarantees.
    Prevents spam filter pattern recognition across bulk campaigns.
    """
    if seed is not None:
        random.seed(seed)

    variations: List[str] = []
    attempts = 0
    while len(variations) < batch_size and attempts < max_attempts:
        attempts += 1
        candidate = expand_spintax(template)
        if not candidate:
            continue
        if not variations:
            variations.append(candidate)
            continue

        distances = [calculate_jaccard_distance(candidate, existing) for existing in variations]
        if all(d >= min_jaccard_distance for d in distances) and candidate not in variations:
            variations.append(candidate)

    if not variations:
        cand = expand_spintax(template)
        if cand:
            variations.append(cand)

    all_distances = []
    for i in range(len(variations)):
        for j in range(i + 1, len(variations)):
            all_distances.append(calculate_jaccard_distance(variations[i], variations[j]))

    avg_dist = sum(all_distances) / len(all_distances) if all_distances else (min_jaccard_distance if len(variations) > 1 else 0.0)
    diversity_tier = (
        "HIGH_ENTROPY_SPAM_IMMUNE"
        if avg_dist >= 0.30
        else ("MODERATE_ENTROPY" if avg_dist >= 0.20 else "LOW_ENTROPY")
    )

    return {
        "count": len(variations),
        "variations": variations,
        "average_jaccard_distance": round(avg_dist, 4),
        "diversity_tier": diversity_tier,
    }

