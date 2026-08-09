"""
Global Salary Negotiation Oracle - JobHunt Pro God-Tier Module
Provides data-backed compensation benchmarking, equity calculation, counter-offer script generation, and verbal call playbooks.
"""

from typing import Dict, List, Any, Optional


class SalaryNegotiationOracle:
    def __init__(self):
        self.regional_multipliers = {
            "us": 1.0,
            "usa": 1.0,
            "gulf": 0.85,
            "uae": 0.90,
            "dubai": 0.92,
            "abu_dhabi": 0.90,
            "ksa": 0.88,
            "riyadh": 0.90,
            "qatar": 0.92,
            "kuwait": 0.85,
            "lebanon": 0.65,
            "egypt": 0.50,
            "jordan": 0.60,
            "europe": 0.75,
            "uk": 0.85,
            "canada": 0.82,
            "germany": 0.78,
            "latam": 0.50,
            "asia": 0.45,
            "remote": 0.80,
            "remote_global": 0.80
        }

        self.base_salary_bands = {
            "software engineer": 120000,
            "senior engineer": 145000,
            "senior software engineer": 150000,
            "lead engineer": 175000,
            "staff engineer": 210000,
            "engineering manager": 190000,
            "full stack developer": 130000,
            "frontend engineer": 125000,
            "backend engineer": 135000,
            "devops / site reliability engineer": 140000,
            "devops engineer": 140000,
            "ai / ml engineer": 165000,
            "ai engineer": 165000,
            "data engineer": 135000,
            "security engineer": 145000,
            "cyber security engineer": 150000,
            "solutions architect": 165000,
            "cloud architect": 170000,
            "product manager": 140000,
            "product designer": 125000,
            "ux/ui designer": 115000,
            "data scientist": 145000,
            "marketing manager": 110000,
            "marketing director": 160000,
            "financial analyst": 105000,
            "finance manager": 135000,
            "hr manager": 105000,
            "qa engineer": 110000
        }

    def get_tax_insights(self, region: str) -> Dict[str, Any]:
        """Returns tax and purchasing power insights based on target region."""
        r_lower = region.lower()
        is_tax_free = any(k in r_lower for k in ["uae", "emirates", "dubai", "abu_dhabi", "ksa", "saudi", "qatar", "kuwait", "bahrain", "oman", "gulf"])
        if is_tax_free:
            return {
                "is_tax_free": True,
                "tax_rate_estimate": "0% Income Tax",
                "note_ar": "المنطقة معفاة تماماً من ضريبة الدخل الشخصي (0%) مما يرفع صافي الراتب والقوة الشرائية الحقيقية.",
                "note_en": "0% Personal Income Tax in this region, maximizing your net take-home compensation."
            }
        else:
            return {
                "is_tax_free": False,
                "tax_rate_estimate": "~25% - 35% Income Tax",
                "note_ar": "تقدير اقتطاعات ضريبة الدخل والضمان الاجتماعي بين 20% إلى 35% حسب الشرائح المحلية.",
                "note_en": "Estimated personal income tax and social contributions range between 20% and 35%."
            }

    def calculate_compensation_oracle(
        self,
        role: str,
        initial_offer: float,
        region: str = "us",
        years_experience: int = 5,
        style: str = "balanced",
        currency: str = "USD",
        offered_bonus: float = 0.0,
        offered_equity: float = 0.0,
        competing_offer: bool = False,
        skills_summary: str = "",
        target_percentage: Optional[float] = None,
        lang: str = "ar"
    ) -> Dict[str, Any]:
        """Calculate recommended counter-offer target, Total Comp breakdown, and negotiation strategy with localized PPP."""
        r_key = region.lower().replace(" ", "_").replace("-", "_")
        
        # Match region prefix or lookup
        mult = 0.80
        for k, v in self.regional_multipliers.items():
            if k in r_key or r_key in k:
                mult = v
                break

        role_clean = role.lower().strip()
        base_benchmark = 135000
        for k, v in self.base_salary_bands.items():
            if k in role_clean or role_clean in k:
                base_benchmark = v
                break

        exp_bonus = min(years_experience * 5000, 40000)
        benchmark_target = (base_benchmark + exp_bonus) * mult

        # Increase factor by target_percentage or style
        if target_percentage is not None and target_percentage > 0:
            increase_factor = 1.0 + (target_percentage / 100.0)
        else:
            style_clean = style.lower().strip()
            if style_clean in ["aggressive", "assertive", "حاسم", "قوي"]:
                increase_factor = 1.25
            elif style_clean in ["executive", "تنفيذي", "استراتيجي"]:
                increase_factor = 1.30
            else:
                increase_factor = 1.18

        style_clean = style.lower().strip()

        recommended_counter = max(initial_offer * increase_factor, benchmark_target * 1.05)
        recommended_counter = round(recommended_counter, -2)

        # Total Compensation calculations
        total_offered = initial_offer + offered_bonus + offered_equity
        sign_on_target = round(recommended_counter * 0.10, -2)

        potential_gain = recommended_counter - initial_offer

        # Generate multi-tone counter emails & verbal call scripts
        scripts = self._generate_multi_tone_scripts(
            role=role,
            region=region,
            initial_offer=initial_offer,
            counter_offer=recommended_counter,
            currency=currency,
            years_exp=years_experience,
            competing_offer=competing_offer,
            skills_summary=skills_summary
        )

        call_scripts = self._generate_verbal_call_scripts(
            role=role,
            region=region,
            counter_offer=recommended_counter,
            currency=currency,
            competing_offer=competing_offer,
            skills_summary=skills_summary
        )

        tax_info = self.get_tax_insights(region)

        pct_boost = int(round(((recommended_counter - initial_offer) / max(initial_offer, 1)) * 100))

        tactics_en = [
            f"Target base salary counter of {currency} {recommended_counter:,.0f} (+{pct_boost}% boost).",
            f"Request a Sign-on Bonus of {currency} {sign_on_target:,.0f} if base budget is capped.",
            "Insert a 6-month performance & compensation review milestone.",
            "Negotiate remote flexibility stipend, equipment allowance, and annual education fund."
        ]

        tactics_ar = [
            f"رفع العرض الأساسي المستهدف إلى {currency} {recommended_counter:,.0f} (بنسبة زيادة +{pct_boost}%).",
            f"المطالبة بمكافأة انضمام ترحيبية (Sign-on Bonus) بمبلغ {currency} {sign_on_target:,.0f} في حال كان السقف المالي محدداً.",
            "إدراج بند مراجعة الأداء والراتب بعد 6 أشهر من استلام العمل.",
            "المطالبة بميزانية التجهيزات السحابية للعمل ومكافأة التطوير المهني والشهادات."
        ]

        objections = self.get_all_objection_rebuttals(
            role=role,
            target_salary=recommended_counter,
            currency=currency,
            lang=lang
        )

        ppp_matrix = self.get_ppp_cost_of_living_matrix(
            base_salary=recommended_counter,
            source_currency=currency
        )

        return {
            "success": True,
            "role": role,
            "region": region,
            "currency": currency,
            "ppp_multiplier": mult,
            "style": style,
            "initial_offer": initial_offer,
            "offered_bonus": offered_bonus,
            "offered_equity": offered_equity,
            "total_offered": total_offered,
            "market_benchmark": round(benchmark_target, -2),
            "recommended_counter_offer": recommended_counter,
            "potential_gain": potential_gain,
            "potential_percentage_gain": round(((recommended_counter - initial_offer) / max(initial_offer, 1)) * 100, 1),
            "counter_email_script": scripts.get(style_clean, scripts.get("balanced")),
            "scripts": scripts,
            "call_scripts": call_scripts,
            "tax_insights": tax_info,
            "negotiation_tactics": tactics_ar if lang == "ar" else tactics_en,
            "negotiation_tactics_ar": tactics_ar,
            "negotiation_tactics_en": tactics_en,
            "objection_rebuttals": objections,
            "ppp_matrix": ppp_matrix
        }

    def get_all_objection_rebuttals(
        self,
        role: str,
        target_salary: float,
        currency: str,
        lang: str = "ar"
    ) -> Dict[str, Dict[str, Any]]:
        """Returns counter-rebuttal strategies for 5 top recruiter pushback scenarios."""
        sym = f"{currency} {target_salary:,.0f}"

        return {
            "budget_capped": {
                "title_ar": "🛡️ الميزانية المحددة للمنصب مغلقة وغير قابلة للتعديل",
                "title_en": "🛡️ Budget for this role is strictly capped",
                "email_ar": f"أفهم تماماً قيود الميزانية المحددة لمنصب {role}. لتجسير الفارق للوصول لـ {sym} دون تجاوز سقف السلم الوظيفي، أقترح إضافة مكافأة انضمام ترحيبية (Sign-on Bonus) أو الجدولة لمراجعة استثنائية للراتب بعد 6 أشهر بناءً على نتائج الأداء.",
                "email_en": f"I completely respect budget constraints for {role}. To bridge the gap towards {sym} without exceeding scale caps, I propose incorporating a one-time sign-on bonus or setting a 6-month performance & compensation review milestone.",
                "verbal_ar": f"\"أقدر صراحتكم بشأن الميزانية. بما أنني حريص جداً على الانضمام، هل يمكننا هيكلة الفارق عن طريق مكافأة انضمام (Sign-on Bonus) لمرة واحدة أو جدولة تقييم أداء مبكر بعد 6 أشهر؟\"",
                "verbal_en": f"\"I understand budget bounds are fixed. Since I am very keen on this team, could we bridge the gap with a one-time sign-on bonus or schedule an accelerated 6-month performance review?\""
            },
            "standard_band": {
                "title_ar": "📊 هذا هو الحد الأعلى لنطاق هذا المستوى الوظيفي",
                "title_en": "📊 This is the top of the pay band for this level",
                "email_ar": f"استناداً إلى النطاق العريض لمسؤوليات {role} والقيمة المضافة للخبرة الحالية، أقترح دراسة تعديل المسمى الوظيفي للمستوى التالي أو تضمين حزمة مزايا مرنة تعوض الفارق للحفاظ على مستهدف {sym}.",
                "email_en": f"Given the scope of work and immediate execution track record, I suggest considering a level title alignment or complementing the package with flexible stipends and equity to reach our {sym} target.",
                "verbal_ar": f"\"أفهم أن هذا أعلى النطاق، ولكن بالنظر لنطاق التأثير المتوقع، هل من الممكن مراجعة المسمى الوظيفي للمستوى الأعلى أو إضافة ميزانية تجهيز وتطوير مهني لتعويض الفارق؟\"",
                "verbal_en": f"\"I understand this touches the top of the band. Given the scope of impact, could we evaluate adjusting the title level or supplementing with an education and remote setup allowance?\""
            },
            "other_candidates": {
                "title_ar": "⏳ لدينا مرشحون آخرون جاهزون للقبول بنفس الراتب",
                "title_en": "⏳ We have other candidates willing to accept this offer",
                "email_ar": f"يسعدني معرفة وجود اهتمام من مرشحين مميزين بالشركة. ثقتي تكمن في الجاهزية الفورية لتسليم المخرجات دون حاجة لفترة تدريب طويلة، وأنا حريص على إتمام الاتفاق عند {sym} للبدء فوراً.",
                "email_en": f"I appreciate that you have a strong talent pool. My core value lies in zero ramp-up time and immediate ROI. I remain fully committed to finalizing our agreement at {sym} and launching right away.",
                "verbal_ar": f"\"أحترم وجود مرشحين آخرين، لكن تميزي يكمن في التنفيذ الفوري والخبرة الميدانية المباشرة. أنا خياركم الجاهز للتوقيع فوراً عند التوافق على {sym}.\"",
                "verbal_en": f"\"I respect that you have other strong options. My value is immediate execution with minimal onboarding. I am ready to sign today if we align on {sym}.\""
            },
            "no_signon": {
                "title_ar": "🚫 سياسة الشركة لا تسمح بمكافآت الانضمام",
                "title_en": "🚫 Company policy prohibits sign-on bonuses",
                "email_ar": f"أفهم السياسات الداخلية للشركة. بدلاً من مكافأة الانضمام، يمكننا النظر في تعديل نسبة البونوس السنوي، أو تسريع استحقاق الأسهم (Vesting Schedule)، أو إضافة بدل عمل مرن.",
                "email_en": f"I respect internal company guidelines. In lieu of a sign-on bonus, we could adjust annual performance bonus targets, accelerate equity vesting schedules, or allocate a remote stipend.",
                "verbal_ar": f"\"تفهمت عدم إمكانية صرف مكافأة انضمام. هل يمكن بدلاً من ذلك ربط الفارق ببونوس الأداء السنوي أو توفير ميزانية تطوير دورات وشهادات احترافية؟\"",
                "verbal_en": f"\"Got it regarding the sign-on policy. Could we instead tie that delta to annual performance incentives or a professional training budget?\""
            },
            "wfh_adjusted": {
                "title_ar": "🏠 الراتب يتضمن ميزة العمل مرناً عن بعد",
                "title_en": "🏠 Remote / Flexible work option offsets base salary",
                "email_ar": f"العمل عن بعد ميزة قيّمة، ولكن التركيز يظل على القيمة الاستراتيجية والنتائج المسلمة للمنصب. لتأكيد التوازن، أقترح اعتماد {sym} كراتب أساسي يضمن أعلى مستويات الالتزام والإنجاز.",
                "email_en": f"While remote flexibility is valuable, total compensation should reflect outcomes delivered. Aligning base pay at {sym} ensures maximum focus and high-impact deliverables.",
                "verbal_ar": f"\"العمل عن بعد ميزة ممتازة، لكن القيمة المنتجة واحدة وساعات العمل كاملة. أطمح لاعتماد {sym} لضمان التفرغ التام وتحقيق الأهداف المطلوبة.\"",
                "verbal_en": f"\"Remote flexibility is great, but the work output and value delivered remain identical. Aligning on {sym} guarantees full commitment to driving key metrics.\""
            }
        }

    def get_ppp_cost_of_living_matrix(
        self,
        base_salary: float,
        source_currency: str = "USD"
    ) -> List[Dict[str, Any]]:
        """Returns regional Purchasing Power Parity (PPP) and tax-adjusted take-home matrix."""
        fx = 1.0
        if source_currency == "AED":
            fx = 0.27
        elif source_currency == "SAR":
            fx = 0.27
        elif source_currency == "QAR":
            fx = 0.27
        elif source_currency == "EUR":
            fx = 1.08
        elif source_currency == "GBP":
            fx = 1.28
        elif source_currency == "EGP":
            fx = 0.021
        elif source_currency == "LBP":
            fx = 0.000011

        base_usd = base_salary * fx

        regions = [
            {"name_ar": "🇦🇪 الإمارات (دبي)", "name_en": "UAE (Dubai)", "tax": 0.0, "ppp_index": 1.10, "curr": "AED", "rate": 3.67},
            {"name_ar": "🇸🇦 السعودية (الرياض)", "name_en": "KSA (Riyadh)", "tax": 0.0, "ppp_index": 1.15, "curr": "SAR", "rate": 3.75},
            {"name_ar": "🇶🇦 قطر (الدوحة)", "name_en": "Qatar (Doha)", "tax": 0.0, "ppp_index": 1.12, "curr": "QAR", "rate": 3.64},
            {"name_ar": "🇺🇸 أمريكا (USA)", "name_en": "United States", "tax": 0.28, "ppp_index": 1.00, "curr": "USD", "rate": 1.0},
            {"name_ar": "🇬🇧 بريطانيا (UK)", "name_en": "United Kingdom", "tax": 0.32, "ppp_index": 0.95, "curr": "GBP", "rate": 0.78},
            {"name_ar": "🇩🇪 ألمانيا (Germany)", "name_en": "Germany", "tax": 0.38, "ppp_index": 0.92, "curr": "EUR", "rate": 0.92},
            {"name_ar": "🇪🇬 مصر (مصر)", "name_en": "Egypt", "tax": 0.20, "ppp_index": 1.85, "curr": "EGP", "rate": 48.5},
            {"name_ar": "🇱🇧 لبنان (لبنان)", "name_en": "Lebanon", "tax": 0.10, "ppp_index": 1.40, "curr": "USD", "rate": 1.0}
        ]

        matrix = []
        for r in regions:
            gross_usd = base_usd
            net_usd = gross_usd * (1.0 - r["tax"])
            real_ppp_usd = net_usd * r["ppp_index"]
            local_gross = gross_usd * r["rate"]
            local_net = net_usd * r["rate"]

            matrix.append({
                "region_ar": r["name_ar"],
                "region_en": r["name_en"],
                "tax_rate_pct": int(r["tax"] * 100),
                "gross_local": round(local_gross, -1),
                "net_local": round(local_net, -1),
                "net_usd": round(net_usd, 0),
                "real_ppp_usd": round(real_ppp_usd, 0),
                "currency": r["curr"]
            })

        return matrix

    def _generate_multi_tone_scripts(
        self,
        role: str,
        region: str,
        initial_offer: float,
        counter_offer: float,
        currency: str,
        years_exp: int,
        competing_offer: bool,
        skills_summary: str
    ) -> Dict[str, Dict[str, str]]:
        skills_txt = skills_summary.strip() or "proven technical mastery and leadership impact"
        competing_str_en = " While I am currently evaluating parallel opportunities offering higher baselines," if competing_offer else ""
        competing_str_ar = " وعلى الرغم من وجود عروض وظيفية موازية أدرسها حالياً بمزايا تنافسية أعلى،" if competing_offer else ""

        # Diplomatic / Balanced
        diplomatic_en = (
            f"Dear Hiring Team,\n\n"
            f"Thank you so much for extending the offer for the {role} position. "
            f"I am genuinely thrilled about the team's vision and confident in driving immediate impact.\n\n"
            f"Based on recent 2026 compensation data for {role} roles in {region} and my {years_exp}+ years of experience in {skills_txt},{competing_str_en} "
            f"I would like to discuss adjusting the base compensation to {currency} {counter_offer:,.0f}.\n\n"
            f"I am fully committed to making this partnership a resounding success and look forward to your thoughts.\n\n"
            f"Warm regards,\nCandidate"
        )
        diplomatic_ar = (
            f"السادة فريق التوظيف المحترمين،\n\n"
            f"أشكركم جزيل الشكر على تقديم العرض الوظيفي لمنصب {role}. "
            f"أنا متحمس للغاية للرؤية المستقبلية للفريق وولدي الثقة الكاملة في تحقيق نتائج ملموسة واستثنائية.\n\n"
            f"استناداً إلى بيانات ومؤشرات الرواتب لعام 2026 لمنصب {role} في منطقة {region} مع خبرتي الممتدة لـ {years_exp} سنوات في {skills_txt}،{competing_str_ar} "
            f"أود اقتراح تعديل الراتب الأساسي ليصل إلى {currency} {counter_offer:,.0f}.\n\n"
            f"أنا ملتزم تماماً بالانضمام وتقديم قيمة مضاعفة، وأتطلع لسماع رأيكم الكريم للتوقيع والبدء فوراً.\n\n"
            f"مع خالص التقدير والاحترام،\nالمترشح"
        )

        # Assertive / High-Value
        assertive_en = (
            f"Hi Hiring Team,\n\n"
            f"Thank you for reaching out with the offer for the {role} role. "
            f"I am very excited about what we can accomplish together.\n\n"
            f"Having reviewed the scope and total compensation package against 2026 market standards in {region}, "
            f"I am aiming for a base salary of {currency} {counter_offer:,.0f}.{competing_str_en}\n\n"
            f"With this baseline in place, I will be ready to sign the agreement immediately and begin driving key outcomes.\n\n"
            f"Best regards,\nCandidate"
        )
        assertive_ar = (
            f"مرحباً فريق التوظيف،\n\n"
            f"شكراً لكم على إرسال تفاصيل العرض الوظيفي لدور {role}. "
            f"أنا مهتم جداً بالقيمة والنتائج التي يمكننا تحقيقها سوياً.\n\n"
            f"بعد مراجعة نطاق المسؤوليات وحزمة التعويضات الحالية مقارنة بمعايير السوق لعام 2026 في {region}، "
            f"أهدف لتحديد الراتب الأساسي عند {currency} {counter_offer:,.0f}.{competing_str_ar}\n\n"
            f"عند الاتفاق على هذا النطاق، سأكون جاهزاً لتوقيع العرض فوراً وبدء العمل على الأولويات المطلوبة.\n\n"
            f"تحياتي،\nالمترشح"
        )

        # Executive / Strategic
        executive_en = (
            f"Dear Executive Team,\n\n"
            f"I appreciate the formal offer for the {role} position. "
            f"The opportunity to step in and accelerate our strategic objectives aligns perfectly with my background.\n\n"
            f"To reflect the strategic impact, domain experience ({skills_txt}), and current market standards for senior leaders in {region}, "
            f"I propose structuring the base component at {currency} {counter_offer:,.0f}, alongside a performance review milestone.{competing_str_en}\n\n"
            f"I am confident this structure will align our mutual incentives and deliver substantial ROI.\n\n"
            f"Sincerely,\nCandidate"
        )
        executive_ar = (
            f"السادة الإدارة التنفيذية وفريق التوظيف،\n\n"
            f"أقدر جداً تقديم العرض الوظيفي الرسمي لمنصب {role}. "
            f"إن فرصة القيادة والمساهمة في تسريع الأهداف الاستراتيجية تتوافق تماماً مع خبرتي ورؤيتي.\n\n"
            f"وليعكس العرض حجم الأثر الإستراتيجي ونطاق الخبرة ({skills_txt}) واستحقاق السوق لعام 2026 في {region}، "
            f"أقترح أن يكون هيكل الراتب الأساسي عند {currency} {counter_offer:,.0f}، مع ربط جزء من الحوافز بمحطات الأداء.{competing_str_ar}\n\n"
            f"أنا على ثقة بأن هذا الهيكل يضمن تحقيق أعلى عائد على الاستثمار واستدامة القيمة.\n\n"
            f"وتفضلوا بقبول فائق الإحترام،\nالمترشح"
        )

        return {
            "balanced": {"en": diplomatic_en, "ar": diplomatic_ar},
            "diplomatic": {"en": diplomatic_en, "ar": diplomatic_ar},
            "assertive": {"en": assertive_en, "ar": assertive_ar},
            "aggressive": {"en": assertive_en, "ar": assertive_ar},
            "executive": {"en": executive_en, "ar": executive_ar}
        }

    def _generate_verbal_call_scripts(
        self,
        role: str,
        region: str,
        counter_offer: float,
        currency: str,
        competing_offer: bool,
        skills_summary: str
    ) -> Dict[str, Dict[str, str]]:
        skills_txt = skills_summary.strip() or "خبرتي الفنية والقيادية"
        competing_ar = " لدي أيضاً فرصة أخرى متقدمة أدرسها حالياً، لكن تفضيلي الأول هو انضمامي لكم." if competing_offer else ""
        competing_en = " I am also evaluating another advanced opportunity, but this position remains my absolute top choice." if competing_offer else ""

        diplomatic_ar = (
            f"📞 سيناريو المكالمة الشفهية (أسلوب دبلوماسي):\n\n"
            f"1️⃣ البدء بالشكر والاهتمام:\n"
            f"\"أهلاً فلان، أشكركم جداً على العرض. أنا مهتم للغاية بالانضمام للعمل على {role}.\"\n\n"
            f"2️⃣ طرح التعديل بدبلوماسية:\n"
            f"\"بعد دراسة مؤشرات السوق لعام 2026 ومتطلبات المنصب، أرى أن الراتب العادل والمتوافق مع النطاق هو {currency} {counter_offer:,.0f}.\"{competing_ar}\n\n"
            f"3️⃣ إظهار المرونة والحسم:\n"
            f"\"إذا استطعنا التقارب عند هذا الرقم، سأكون جاهزاً للتوقيع والبدء فوراً!\""
        )

        diplomatic_en = (
            f"📞 Phone Call Verbal Script (Diplomatic Tone):\n\n"
            f"1️⃣ Express Gratitude & Excitement:\n"
            f"\"Thank you so much for extending the offer. I'm really excited about the {role} role and driving impact with the team.\"\n\n"
            f"2️⃣ State the Counter Baseline:\n"
            f"\"Based on 2026 market benchmarks and my core background in {skills_txt}, I am looking to align the base salary at {currency} {counter_offer:,.0f}.\"{competing_en}\n\n"
            f"3️⃣ Close with Readiness:\n"
            f"\"If we can bridge this gap, I am ready to sign and start immediately!\""
        )

        assertive_ar = (
            f"📞 سيناريو المكالمة الشفهية (أسلوب حاسم):\n\n"
            f"1️⃣ المباشرة والوضوح:\n"
            f"\"أهلاً فلان، شكراً على العرض الوظيفي لـ {role}. القيمة والمسؤوليات واضحة ومتحمس جداً للنتائج.\"\n\n"
            f"2️⃣ تحديد المستهدف بوضوح:\n"
            f"\"لتأكيد الانضمام، أود اعتماد الراتب الأساسي عند {currency} {counter_offer:,.0f} بناءً على قيمتي السوقية وقدرتي على تسليم المشاريع من اليوم الأول.\"\n\n"
            f"3️⃣ إتاحة بديل المكافأة الترحيبية:\n"
            f"\"في حال كان هناك سقف مالي للراتب الأساسي، يمكننا التعويض بمكافأة انضمام (Sign-on Bonus).\""
        )

        assertive_en = (
            f"📞 Phone Call Verbal Script (Assertive Tone):\n\n"
            f"1️⃣ Direct & Confident Opening:\n"
            f"\"Hi team, thanks for sending over the offer details for {role}. I appreciate the clarity on responsibilities.\"\n\n"
            f"2️⃣ Firm Counter Target:\n"
            f"\"To confirm my commitment right away, I am looking for {currency} {counter_offer:,.0f} base salary based on market rates and immediate execution value.\"\n\n"
            f"3️⃣ Sign-on Option:\n"
            f"\"If the base cap is strictly fixed, we can bridge the difference via a sign-on bonus or structured review.\""
        )

        executive_ar = (
            f"📞 سيناريو المكالمة الشفهية (أسلوب تنفيذي):\n\n"
            f"1️⃣ التركيز على الأثر الاستراتيجي والعائد:\n"
            f"\"مرحباً، أقدر العرض الرسمي لقيادة {role}. الرؤية الاستراتيجية واعدة وأنا ملائم تماماً لتنفيذها.\"\n\n"
            f"2️⃣ اقتراح الهيكل الاستراتيجي:\n"
            f"\"ليضمن الهيكل تحقيق أعلى عائد واستدامة، أقترح ضبط الراتب الأساسي عند {currency} {counter_offer:,.0f} مع ربط الحوافز بالأهداف الكبرى.\"\n\n"
            f"3️⃣ إنهاء المكالمة بثقة:\n"
            f"\"أتطلع لتأكيد الهيكل النهائي لتوقيع الاتفاقية والانطلاق.\""
        )

        executive_en = (
            f"📞 Phone Call Verbal Script (Executive Tone):\n\n"
            f"1️⃣ Strategic Value Focus:\n"
            f"\"Hello, thank you for the formal offer to lead {role}. The strategic roadmap aligns directly with my executive track record.\"\n\n"
            f"2️⃣ Proposed Compensation Structure:\n"
            f"\"To ensure mutual alignment on long-term ROI, I propose structuring the base component at {currency} {counter_offer:,.0f} alongside clear milestone incentives.\"\n\n"
            f"3️⃣ Executive Commitment:\n"
            f"\"Let me know your thoughts so we can finalize the structure and initiate onboarding.\""
        )

        return {
            "diplomatic": {"en": diplomatic_en, "ar": diplomatic_ar},
            "balanced": {"en": diplomatic_en, "ar": diplomatic_ar},
            "assertive": {"en": assertive_en, "ar": assertive_ar},
            "aggressive": {"en": assertive_en, "ar": assertive_ar},
            "executive": {"en": executive_en, "ar": executive_ar}
        }


salary_oracle = SalaryNegotiationOracle()


