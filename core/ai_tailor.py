"""
AITailor v2 - Groq-Powered Personalized CV Tailoring & Cover Letter Generation
Uses Groq's llama3-70b-8192 (primary) / mixtral-8x7b-32768 (fallback)
with async calls, structured prompts, and graceful fallbacks.
"""
import json
import logging
import re
import httpx
import asyncio
import hashlib
import config
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import core.semantic_cache as semantic_cache

logger = logging.getLogger(__name__)

# ── Candidate profile (single source of truth) ──────────────────────────────
CANDIDATE_PROFILE = {
    "name": "Sam Salameh",
    "title": "Senior Network Engineer",
    "years": 15,
    "core_skills": [
        "Cisco (CCNA/CCNP)", "MikroTik (MTCNA/MTCRE)", "Fortinet (NSE)",
        "Ubiquiti", "Juniper", "Palo Alto", "SonicWall", "Checkpoint",
        "SD-WAN (Silver Peak/Viptela)", "SASE", "ZTNA", "Zero Trust Architecture",
        "SDN", "Network Automation", "NetDevOps", "NFV", "VXLAN", "EVPN",
        "Segment Routing", "IPv6", "Multicast", "QoS", "Load Balancing (F5/NGINX)",
        "Cisco ACI", "VMware NSX", "Meraki", "Aruba", "Ruckus", "ExtremeNetworks",
        "Riverbed", "Blue Coat", "Zscaler", "Cloudflare", "Akamai CDN"
    ],
    "protocols": [
        "OSPF", "BGP", "MPLS", "VPN", "IPSec", "VLAN", "WLAN", "WAN/LAN",
        "VXLAN", "EVPN", "IS-IS", "EIGRP", "STP", "RSTP", "MSTP", "LACP",
        "MLAG", "VRRP", "HSRP", "GLBP", "PIM", "IGMP", "SNMP", "NetFlow",
        "sFlow", "IPFIX", "RADIUS", "TACACS+", "802.1X", "MACsec", "DMVPN",
        "GETVPN", "FlexVPN", "L2TP", "PPTP", "GRE", "IP-in-IP"
    ],
    "security": [
        "Firewalls (FortiGate/Palo Alto/Checkpoint)", "IDS/IPS", "Network Security",
        "Zero Trust / ZTNA", "SASE", "NGFW", "WAF", "DLP", "SIEM (Splunk/ELK)",
        "SOAR", "Endpoint Security", "EDR/XDR", "IAM", "PAM", "MFA",
        "PKI", "SSL/TLS", "IPSec VPN", "DMZ Architecture", "Micro-segmentation",
        "NAC (Cisco ISE/Aruba ClearPass)", "Threat Intelligence", "Vulnerability Management",
        "Penetration Testing", "SOC Operations", "Incident Response", "Forensics"
    ],
    "monitoring": [
        "PRTG", "Nagios", "Zabbix", "SolarWinds", "Wireshark",
        "Prometheus", "Grafana", "ELK Stack (Elasticsearch/Logstash/Kibana)",
        "Splunk", "Datadog", "New Relic", "LibreNMS", "Observium",
        "Cacti", "MRTG", "Smokeping", "NetCrunch", "WhatsUp Gold",
        "LogicMonitor", "AppDynamics", "Dynatrace"
    ],
    "cloud": [
        "AWS (VPC/Direct Connect/Route53)", "Azure (ExpressRoute/VNet)",
        "GCP (Cloud Interconnect/VPC)", "VMware vSphere/vCenter", "Hyper-V",
        "Docker", "Kubernetes", "Istio Service Mesh", "Terraform",
        "AWS CloudFormation", "Azure ARM", "GCP Deployment Manager",
        "OCI (Oracle Cloud)", "OpenStack", "Cloud Networking", "SDN"
    ],
    "automation": [
        "Python (Netmiko/Napalm/Scrapli/Nornir)", "PowerShell", "Ansible (AWX/Tower)",
        "Terraform (IaC)", "Bash/Shell Scripting", "Git (GitHub/GitLab/Bitbucket)",
        "CI/CD (Jenkins/GitLab CI/GitHub Actions)", "Docker", "Kubernetes",
        "REST APIs (Postman/cURL)", "YAML/JSON/XML", "Jinja2 Templating",
        "Robot Framework", "PyATS/genie", "SaltStack", "Puppet", "Chef",
        "ELK Stack Automation", "NetBox/IPAM Automation", "NAPALM Automation"
    ],
    "infrastructure": [
        "Data Center Design (Tier III/IV)", "Fiber Optic (Single/Multi-mode)",
        "Structured Cabling (Cat6a/Cat7/Fiber)", "Wireless Networks (Wi-Fi 6/6E)",
        "MPLS WAN Design", "SD-WAN Architecture", "Campus LAN Design",
        "Branch Office Networking", "Colocation Management", "DR Site Design",
        "BGP/OSPF Route Optimization", "QoS Design", "Multicast Design",
        "IPv6 Migration", "Network Segmentation", "DC Interconnect (DCI)"
    ],
    "certs": [
        "CCNA", "CCNP", "CCIE (Written)", "MTCNA", "MTCRE", "MTCINE",
        "NSE 4", "NSE 5", "NSE 6", "NSE 7", "CompTIA Network+",
        "CompTIA Security+", "AWS Certified Solutions Architect",
        "Azure Network Engineer Associate", "ITIL Foundation",
        "Palo Alto PCNSA", "Juniper JNCIA", "Cisco DevNet Associate",
        "Fortinet FCP", "VMware VCP-NV", "Certified Kubernetes Administrator (CKA)"
    ],
    "highlights": [
        "15+ years designing and managing enterprise networks across 10+ countries (Lebanon, UAE, Saudi Arabia, Qatar, Kuwait, Oman, Jordan, Egypt, Turkey, Iraq)",
        "Designed and deployed SD-WAN solution across 50+ sites reducing WAN costs by 45% while improving application performance by 60%",
        "Implemented Zero Trust Network Access (ZTNA/SASE) architecture securing 2,000+ remote users across 30+ branch offices",
        "Led migration of 100+ servers and network infrastructure to AWS/Azure cloud with 99.99% uptime and zero security incidents",
        "Architected multi-site MPLS/VPN backbone connecting 200+ locations with BGP/OSPF route optimization and QoS",
        "Automated network provisioning and configuration management using Ansible/Terraform/Python, reducing deployment time by 40% and operational overhead by 35%",
        "Resolved 50+ daily complex technical issues (Tier 3 escalation) with 98% satisfaction score and <15min average resolution time",
        "Managed $5M+ network infrastructure budget including vendor negotiations, procurement, and lifecycle management",
        "Led SOC/NOC team of 12 engineers, establishing 24/7 monitoring with Splunk/ELK SIEM reducing MTTR by 55%",
        "Designed and implemented enterprise-wide firewall migration (Checkpoint → FortiGate) across 100+ sites with zero downtime",
        "Deployed Wi-Fi 6/6E wireless infrastructure serving 5,000+ concurrent users with seamless roaming and 99.9% availability",
        "Established disaster recovery and business continuity plan with RPO <15min and RTO <2hrs for critical network services",
        "Conducted 50+ security audits and penetration tests, achieving ISO 27001 compliance and passing all regulatory requirements",
        "Mentored 20+ junior engineers, creating training programs that improved team certification pass rate by 70%",
        "Reduced annual network operational costs by $500K+ through automation, vendor consolidation, and optimized licensing"
    ],
}


class AITailor:
    """Groq-powered AI tailoring engine with async calls and fallbacks."""

    # Model priority: llama-3.3-70b for quality, llama-3.1-8b for speed, qwen3 for variety
    MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"]

    def __init__(self):
        self.groq_key = config.GROQ_API_KEY
        self.gemini_key = getattr(config, "GEMINI_API_KEY", "")
        self._client = None  # lazy httpx client
        
        # Initialize LLM Provider Pool (17 rotating providers, $0 cost)
        try:
            from core.llm_provider_pool import LLMProviderPool
            self.llm_pool = LLMProviderPool().initialize()
            logger.info("AITailor: LLMProviderPool initialized successfully.")
        except Exception as e:
            logger.warning(f"AITailor: Failed to initialize LLMProviderPool: {e}")
            self.llm_pool = None

    # ── Public API ───────────────────────────────────────────────────────────

    @staticmethod
    def trim_cv_text(cv_text: str) -> str:
        """Strips filler words and reduces token usage for AI processing."""
        if not cv_text:
            return ""
        stop_words = {"a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
                      "when", "where", "how", "then", "so", "than", "is", "are", "was", "were",
                      "be", "been", "being", "have", "has", "had", "do", "does", "did", "to",
                      "from", "in", "out", "on", "off", "over", "under", "again", "further",
                      "then", "once"}
        words = cv_text.split()
        trimmed = [w for w in words if w.lower() not in stop_words]
        return " ".join(trimmed)

    def get_dynamic_cv_context(self, title: str) -> str:
        """Dynamically build CV context based on target job title."""
        context = [
            f"Candidate: {CANDIDATE_PROFILE['name']}",
            f"Target/Current Title: {CANDIDATE_PROFILE['title']}",
            f"Experience: {CANDIDATE_PROFILE['years']} years",
            f"Certifications: {', '.join(CANDIDATE_PROFILE['certs'])}",
            f"Core Skills: {', '.join(CANDIDATE_PROFILE['core_skills'])}",
            f"Protocols: {', '.join(CANDIDATE_PROFILE['protocols'])}",
            f"Security: {', '.join(CANDIDATE_PROFILE['security'])}",
            f"Automation: {', '.join(CANDIDATE_PROFILE['automation'])}",
            f"Infrastructure: {', '.join(CANDIDATE_PROFILE['infrastructure'])}",
            "Key Achievements:"
        ]
        for highlight in CANDIDATE_PROFILE['highlights']:
            context.append(f"- {highlight}")
            
        # Try to append raw text from the CV PDF if available
        try:
            import os
            import config
            from core.resume_optimizer import ResumeOptimizer
            cv_path = getattr(config, "CV_PATH", "")
            if cv_path and os.path.exists(cv_path):
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If event loop is already running, we can't use asyncio.run.
                    # Since _load_cv_text is a staticmethod that does blocking I/O anyway (no actual await),
                    # we can run its synchronous equivalent or run it in an executor.
                    # Actually, _load_cv_text has no real async calls, it's just async def because of standardizing,
                    # so we can execute it using a future or a thread.
                    # Or simpler, we can just call a synchronous helper, or since _load_cv_text is async,
                    # we can use a thread pool or run_coroutine_threadsafe.
                    # Wait, let's look at _load_cv_text in resume_optimizer.py:
                    # It has no await except in the signature: `async def _load_cv_text`. It just reads files.
                    # So we can run it safely using:
                    # `raw_text = loop.run_until_complete(ResumeOptimizer._load_cv_text(cv_path))`
                    # but since the loop is already running (we are in an async method), we can do:
                    # `raw_text = asyncio.run_coroutine_threadsafe(ResumeOptimizer._load_cv_text(cv_path), loop).result()`
                    # or just run the file reading synchronously ourselves!
                    ext = os.path.splitext(cv_path)[1].lower()
                    if ext in (".txt", ".md", ".rtf"):
                        with open(cv_path, "r", encoding="utf-8", errors="replace") as f:
                            raw_text = f.read()
                    elif ext == ".pdf":
                        import pdfplumber
                        with pdfplumber.open(cv_path) as pdf:
                            raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    else:
                        raw_text = ""
                else:
                    raw_text = asyncio.run(ResumeOptimizer._load_cv_text(cv_path))
                
                if raw_text:
                    context.append("\nFull CV Text:")
                    context.append(raw_text[:2000])
        except Exception as e:
            logger.debug(f"Failed to append raw CV text: {e}")
            
        return "\n".join(context)

    async def score_job_relevance(self, title: str, description: str, company: str = "") -> dict:
        """Score job relevance 0-100 before applying. Returns {score, reasons, recommendation}."""
        cv_text = self.get_dynamic_cv_context(title)
        cv_text = self.trim_cv_text(cv_text)
        
        prompt = f"""You are a job-matching AI. Score how well this candidate matches the job.
Candidate CV summary:
{cv_text[:3000]}

CANDIDATE: {CANDIDATE_PROFILE['name']} — {CANDIDATE_PROFILE['title']}, {CANDIDATE_PROFILE['years']} years experience.
Full skills inventory: {', '.join(CANDIDATE_PROFILE['core_skills'] + CANDIDATE_PROFILE['protocols'] + CANDIDATE_PROFILE['security'] + CANDIDATE_PROFILE['cloud'] + CANDIDATE_PROFILE['automation'] + CANDIDATE_PROFILE['monitoring'] + CANDIDATE_PROFILE['infrastructure'] + CANDIDATE_PROFILE['certs'])[:2000]}

JOB: {title} at {company}
Description: {description[:2000]}

Score 0-100 based on:
1. Skills match (40 pts) — how many required skills does the candidate have? (Be generous: candidate has 15+ years of broad networking/security/cloud/automation expertise)
2. Experience level (25 pts) — does the candidate's 15+ years match the seniority?
3. Domain relevance (25 pts) — is this in the candidate's domain (networking, security, cloud, infrastructure, automation)?
4. Location/culture fit (10 pts) — any obvious mismatches?

IMPORTANT: This candidate has deep expertise across enterprise networking, SD-WAN, SASE, ZTNA, cloud (AWS/Azure/GCP), automation (Python/Ansible/Terraform), security (FortiGate/Palo Alto/Zero Trust), and data center technologies. Be inclusive — if the job is even remotely related to IT infrastructure, networking, or security, score it fairly.

Return ONLY valid JSON:
{{"score": <0-100>, "skills_match": <list of matching skills>, "missing_skills": <list>, "experience_fit": <bool>, "domain_fit": <bool>, "recommendation": "apply"|"maybe"|"skip", "reason": "<1 sentence>"}}"""

        result = await self._call_ai(prompt, max_tokens=500, temperature=0.3)
        if result:
            try:
                # Try to extract JSON from the response (model may wrap in markdown)
                json_str = self._extract_json(result)
                data = json.loads(json_str)
                # Validate score range
                data["score"] = max(0, min(100, int(data.get("score", 0))))
                if "recommendation" not in data:
                    s = data["score"]
                    data["recommendation"] = "apply" if s >= 70 else ("maybe" if s >= 50 else "skip")
                return data
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse relevance score JSON: {e}")

        # Fallback: Vector math scoring
        return self._cosine_similarity_score(title, description)

    async def tailor_cover_letter(self, company: str, title: str, description: str,
                                   company_info: dict = None, language: str = "en") -> str:
        """Generate a personalized cover letter based on job description + company research."""
        company_context = ""
        if company_info:
            company_context = f"""
COMPANY RESEARCH:
- Overview: {company_info.get('info', 'N/A')}
- Recent news: {company_info.get('news', 'N/A')}
- Culture: {company_info.get('culture', 'N/A')}
- Values: {company_info.get('values', 'N/A')}"""

        lang_instruction = ""
        if language == "ar":
            lang_instruction = "\nWrite the cover letter in Arabic (formal business Arabic). Keep it professional and culturally appropriate for Middle East companies."
        elif language == "bilingual":
            lang_instruction = "\nWrite the cover letter in BOTH Arabic and English. Arabic version first, then English version below it, separated by a horizontal line."

        # Dynamic RAG: Only send relevant CV chunks to save tokens and speed up generation
        cv_subset = []
        cv_subset.append(f"- Title: {CANDIDATE_PROFILE['title']}, {CANDIDATE_PROFILE['years']}+ years experience")
        
        job_lower = (title + " " + description).lower()
        if any(k in job_lower for k in ['network', 'cisco', 'fortinet', 'juniper', 'router', 'switch', 'bgp', 'sd-wan', 'sase', 'mpls']):
            cv_subset.append(f"- Core expertise: {', '.join(CANDIDATE_PROFILE['core_skills'])}")
            cv_subset.append(f"- Protocols: {', '.join(CANDIDATE_PROFILE['protocols'])}")
            cv_subset.append(f"- Infrastructure: {', '.join(CANDIDATE_PROFILE['infrastructure'])}")
        
        if any(k in job_lower for k in ['security', 'firewall', 'ips', 'ids', 'zero trust', 'ztna', 'sase', 'siem', 'soc', 'cyber']):
            cv_subset.append(f"- Security: {', '.join(CANDIDATE_PROFILE['security'])}")
            
        if any(k in job_lower for k in ['cloud', 'aws', 'azure', 'gcp', 'vmware', 'kubernetes', 'docker', 'container']):
            cv_subset.append(f"- Cloud: {', '.join(CANDIDATE_PROFILE['cloud'])}")
            
        if any(k in job_lower for k in ['automation', 'python', 'ansible', 'terraform', 'scripting', 'devops', 'ci/cd', 'netdevops']):
            cv_subset.append(f"- Automation: {', '.join(CANDIDATE_PROFILE['automation'])}")
            
        if any(k in job_lower for k in ['monitoring', 'observability', 'splunk', 'prometheus', 'grafana', 'elk', 'siem']):
            cv_subset.append(f"- Monitoring/Observability: {', '.join(CANDIDATE_PROFILE['monitoring'])}")
            
        cv_subset.append(f"- Certifications: {', '.join(CANDIDATE_PROFILE['certs'])}")
        cv_subset.append(f"- Key achievements: {'; '.join(CANDIDATE_PROFILE['highlights'][:3])}") # Top 3 achievements

        prompt = f"""Write a highly personalized, professional cover letter for {CANDIDATE_PROFILE['name']} applying for {title} at {company}.

CANDIDATE PROFILE (RAG Sub-selection):
{chr(10).join(cv_subset)}

JOB DESCRIPTION:
{description[:2500]}
{company_context}
{lang_instruction}

REQUIREMENTS:
1. Professional tone, confident but not arrogant
2. Under 350 words (per language version if bilingual)
3. Highlight ONLY the skills that match the job description — be specific
4. Include a company-specific icebreaker referencing their recent work, values, or projects
5. Quantify achievements where possible
6. Close with a clear call to action
7. Do NOT use generic phrases like "I am writing to express my interest" — start with something compelling
8. Embed the company name ({company}) naturally throughout the letter — in the opening, middle body, and closing — at least 3 distinct mentions
9. Sign as: Sam Salameh, {config.CANDIDATE_EMAIL}, {config.CANDIDATE_PHONE}"""

        result = await self._call_ai(prompt, max_tokens=1500, temperature=0.7)
        return result or None

    async def generate_ats_white_text(self, company: str, title: str, description: str) -> str:
        """
        [THE RAG ATS DOMINATOR]
        Extracts exactly the keywords the ATS is looking for from the Job Description,
        so they can be injected as invisible white text into the candidate's PDF.
        """
        prompt = f"""You are an ATS (Applicant Tracking System) hacking AI.
Read this job description and extract the exact 30-40 keywords, software names, and skills that the ATS parser is scanning for.

JOB DESCRIPTION for {title} at {company}:
{description[:2500]}

Format: Return ONLY a raw comma-separated list of the 30-40 most critical keywords and phrases, separated by commas. No formatting, no bullet points, no introduction. Just the raw keywords."""

        result = await self._call_ai(prompt, max_tokens=200, temperature=0.1)
        return result or "network engineering, infrastructure, security, ccna, ccnp"

    async def optimize_semantic_density(self, company: str, title: str, description: str, current_cv_text: str) -> str:
        """
        [THE ABSOLUTE MAXIMUM]
        Legally optimizes CV semantic density by using Llama3 to perfectly align bullet points 
        with the exact verbiage expected by the ATS, without using hidden text.
        """
        prompt = f"""You are a master ATS optimization engine. 
Rewrite the following CV text so that it achieves >95% semantic overlap with the job description.
Do NOT lie or invent experience. Instead, change the verbiage, terminology, and phrasing of the candidate's actual experience to perfectly match the terminology used in the job description.

CANDIDATE'S CURRENT CV TEXT:
{current_cv_text}

JOB DESCRIPTION FOR {title} AT {company}:
{description[:2500]}

Rewrite the CV text bullet points to maximize keyword density perfectly. Return ONLY the rewritten text."""

        result = await self._call_ai(prompt, max_tokens=1500, temperature=0.5)
        return result or current_cv_text

    async def tailor_cv_summary(self, company: str, title: str, description: str) -> str:
        """Generate a tailored CV summary highlighting the most relevant skills for this specific job."""
        prompt = f"""Write a 3-4 line professional CV summary for {CANDIDATE_PROFILE['name']}, tailored for {title} at {company}.

CANDIDATE: {CANDIDATE_PROFILE['title']}, {CANDIDATE_PROFILE['years']}+ years
All skills: {', '.join(CANDIDATE_PROFILE['core_skills'] + CANDIDATE_PROFILE['protocols'] + CANDIDATE_PROFILE['automation'] + CANDIDATE_PROFILE['cloud'])}
Certifications: {', '.join(CANDIDATE_PROFILE['certs'])}
Key achievements: {'; '.join(CANDIDATE_PROFILE['highlights'])}

JOB REQUIREMENTS (prioritize matching these):
{description[:1500]}

RULES:
1. Lead with the most relevant qualification for THIS specific job
2. Include 2-3 specific technical skills that match the job description
3. Mention a quantified achievement relevant to the role
4. Keep it under 80 words
5. Do NOT use first person ("I") — CV summaries are written in implied first person
6. Be specific, not generic — avoid "results-driven professional" type phrases"""

        result = await self._call_ai(prompt, max_tokens=300, temperature=0.5)
        return result or None

    async def generate_icebreaker(self, company: str, title: str,
                                  description: str = "", company_info: dict = None) -> str:
        """Generate a company-specific icebreaker line for the cover letter."""
        context = f"Job: {title} at {company}"
        if description:
            context += f"\nJob context: {description[:500]}"
        if company_info:
            context += f"\nCompany info: {json.dumps(company_info, ensure_ascii=False)[:500]}"

        prompt = f"""Generate ONE compelling, specific icebreaker sentence for a cover letter.
{context}

The icebreaker should:
1. Reference something specific about the company (recent project, value, achievement, or industry position)
2. Connect it naturally to the candidate's expertise
3. Be 1-2 sentences maximum
4. Sound genuine, not generic — avoid "I admire your company" type phrases
5. If no specific company info is available, reference the industry or role type specifically

Return ONLY the icebreaker text, nothing else."""

        result = await self._call_ai(prompt, max_tokens=150, temperature=0.8)
        return result.strip() if result else f"I am particularly drawn to the {title} opportunity at {company} as it aligns with my extensive network engineering background."

    async def research_company(self, company: str) -> dict:
        """Research a company using AI. Returns structured company info."""
        prompt = f"""Research {company} and provide structured information:
1. Company overview (2-3 sentences)
2. Recent news/achievements (1-2 items)
3. Work culture and values
4. Typical salary range for network engineers in their region
5. Glassdoor rating if known
6. LinkedIn company page URL
7. Career page URL
8. Industry and main products/services
9. Company size (employees)
10. Headquarters location

Format as JSON with keys: info, news, culture, values, salary, glassdoor, linkedin, career_page, industry, size, hq
Only include information you are confident about. Use empty string for unknown fields."""

        result = await self._call_ai(prompt, max_tokens=800, temperature=0.3)
        if result:
            try:
                json_str = self._extract_json(result)
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                return {"info": result[:500], "news": "", "culture": "", "values": "",
                        "salary": "", "glassdoor": "", "linkedin": "", "career_page": "",
                        "industry": "", "size": "", "hq": ""}
        return {}

    async def build_knowledge_graph_intro(self, recruiter_name: str, company: str) -> str:
        """
        [THE ABSOLUTE MAXIMUM]
        Scrapes background data to find mutual connections or shared experiences,
        crafting a 'warm intro' instead of a cold email.
        """
        prompt = f"""You are a master social engineer and networking expert.
I am reaching out to {recruiter_name} at {company}.
Simulate a deep knowledge graph search. In a real scenario, this would use LinkedIn/Clearbit APIs to find a mutual connection or shared background (e.g., same university, previous company, shared interest in a specific networking technology).

Write ONE highly personalized, warm introductory sentence that I can use in an email to {recruiter_name}, making it sound like a warm introduction rather than a cold pitch. 
Assume we both have a background or mutual connection in enterprise networking (Cisco/Fortinet).
Return ONLY the introductory sentence."""

        result = await self._call_ai(prompt, max_tokens=150, temperature=0.7)
        return result or f"Hi {recruiter_name}, noticed we share a mutual passion for enterprise networking and I've been following {company}'s recent infrastructure growth."

    async def generate_interview_prep(self, company: str, title: str, description: str = "") -> list:
        """Generate interview questions and answers tailored to the job."""
        prompt = f"""Generate 10 likely interview questions for {title} at {company} with ideal answers for {CANDIDATE_PROFILE['name']} ({CANDIDATE_PROFILE['years']} years network engineering, {', '.join(CANDIDATE_PROFILE['core_skills'][:5])} expert).
Job context: {description[:500]}

Format as JSON array:
[{{"q": "question text", "a": "ideal answer for this candidate"}}]

Include a mix of:
- Technical questions (routing, security, protocols)
- Scenario-based questions (troubleshooting, design)
- Behavioral questions (leadership, conflict resolution)
- Company-specific questions (why this company, cultural fit)"""

        result = await self._call_ai(prompt, max_tokens=2000, temperature=0.5)
        if result:
            try:
                json_str = self._extract_json(result)
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                # Fallback: parse Q:/A: format
                items = []
                for line in result.split("\n"):
                    if "A:" in line:
                        parts = line.split("A:", 1)
                        q = parts[0].replace("Q:", "").strip()
                        a = parts[1].strip()
                        if q:
                            items.append({"q": q, "a": a})
                return items[:10]
        return []

    async def categorize_response(self, response_text: str) -> str:
        """Categorize an email response from a company."""
        prompt = f"Categorize this email response into one of: reject, interview_request, offer, spam, neutral, follow_up_needed. Response: {response_text[:500]}\nReturn ONLY the category name, nothing else."
        result = await self._call_ai(prompt, max_tokens=20, temperature=0.1)
        return result.strip().lower() if result else "neutral"

    async def generate_thank_you(self, company: str, title: str, interview_date: str = "") -> str:
        """Generate a post-interview thank you email."""
        date_context = f" after the interview on {interview_date}" if interview_date else ""
        prompt = f"Write a brief thank-you email for {CANDIDATE_PROFILE['name']}{date_context} for a {title} interview at {company}. Professional, reference specific discussion points about network engineering, express continued interest. Under 150 words."
        result = await self._call_ai(prompt, max_tokens=300, temperature=0.6)
        return result or None

    # ── AI Call Layer (Groq primary, Gemini fallback) ────────────────────────
    
    _SEMANTIC_CACHE = {} # Local memory fallback

    async def _call_ai(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str | None:
        """Call AI with pgvector Semantic Caching → Rotating LLM Provider Pool → Legacy Hardcoded Groq/Gemini fallback.
        Includes a self-healing retry mechanism that detects unresolved placeholders in the AI response,
        re-prompts the model with strict formatting guidelines if found, and falls back gracefully to templates.
        """
        
        # 1. $0 pgvector Semantic Caching Layer
        try:
            cached_res = semantic_cache.get_cached_response(prompt)
            if cached_res:
                logger.info(f"[$0 PGVECTOR SEMANTIC CACHE HIT] Saved {max_tokens} tokens.")
                return cached_res
        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {e}")

        # Helper to validate response content
        def _is_valid_ai_response(text: str) -> bool:
            if not text:
                return False
            unresolved_placeholders = [
                '{first_name}', '{company}', '{position}', '{title}', '{company_name}',
                '[Company Name]', '[Recruiter Name]', '[Job Title]', '[Insert',
                '<first_name>', '<company>', '<position>'
            ]
            has_unresolved = any(placeholder.lower() in text.lower() for placeholder in unresolved_placeholders)
            has_empty_braces = bool(re.search(r'\{\s*\}|\[\s*\]|<\s*>', text))
            return not (has_unresolved or has_empty_braces)

        # Local cache fallback
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        if cache_key in self._SEMANTIC_CACHE:
            cached_val = self._SEMANTIC_CACHE[cache_key]
            if _is_valid_ai_response(cached_val):
                return cached_val
            else:
                del self._SEMANTIC_CACHE[cache_key]

        current_prompt = prompt
        for attempt in range(1, 4):
            result = None

            # 2. Try rotating LLM Provider Pool (17 providers, non-blocking, automatic 429 rotation)
            if self.llm_pool:
                try:
                    result = await self.llm_pool.complete(
                        system_prompt="You are a professional career advisor and cover letter writer. Always follow the user's formatting instructions precisely. When asked for JSON, return ONLY valid JSON without markdown code fences.",
                        user_prompt=current_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                except Exception as e:
                    logger.warning(f"Rotating LLM Provider Pool failed on attempt {attempt}: {e}. Falling back to legacy Groq/Gemini...")

            # 3. Legacy Fallback: Try Groq first (fast, free tier)
            if not result and self.groq_key:
                for model in self.MODELS:
                    try:
                        result = await self._call_groq(current_prompt, model, max_tokens, temperature)
                        if result:
                            break
                    except Exception as e:
                        logger.warning(f"Groq {model} failed on attempt {attempt}: {e}")
                        continue

            # 4. Legacy Fallback: Try Gemini
            if not result and self.gemini_key:
                try:
                    result = await self._call_gemini(current_prompt, max_tokens)
                except Exception as e:
                    logger.warning(f"Gemini failed on attempt {attempt}: {e}")

            # Validate the response content
            if result:
                if _is_valid_ai_response(result):
                    # Valid response! Save and return.
                    self._SEMANTIC_CACHE[cache_key] = result
                    try:
                        semantic_cache.save_to_cache(prompt, result)
                    except:
                        pass
                    return result
                else:
                    logger.warning(
                        f"[Self-Healing AI] Attempt {attempt} generated a response with unresolved placeholders! "
                        "Retrying with stricter directives..."
                    )
                    # Modify prompt to strictly forbid placeholders
                    current_prompt = (
                        prompt +
                        "\n\nCRITICAL DIRECTIVE: Do NOT output any template placeholders, brackets, or braces "
                        "(e.g., NO '[Company Name]', '{first_name}', '[Job Title]', or empty brackets like '[]' or '{}'). "
                        "Write out the actual candidate name, job title, and company directly. If you do not know a detail, "
                        "write a realistic name or generic phrase instead of a placeholder."
                    )
                    # Slightly increase temperature to get a different completion path
                    temperature = min(1.0, temperature + 0.1)

        logger.error("[Self-Healing AI] All AI providers failed or generated invalid responses after 3 attempts.")
        return None

    async def _call_groq(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str | None:
        """Call Groq API with a specific model.
        Handles TPD (tokens-per-day) exhaustion gracefully: if the 429 error
        mentions TPD, skip retry immediately since the limit won't reset for hours.
        Otherwise, retry once after a brief wait.
        """
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional career advisor and cover letter writer. Always follow the user's formatting instructions precisely. When asked for JSON, return ONLY valid JSON without markdown code fences."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip() if content else None
            elif resp.status_code == 429:
                error_text = resp.text.lower()
                if "tpd" in error_text or "tokens per day" in error_text:
                    logger.warning(f"Groq {model} TPD limit exhausted, skipping retry: {error_text[:100]}")
                    raise Exception(f"Groq {model} TPD exhausted — {error_text[:100]}")
                
                logger.warning(f"Groq rate limited on {model}, waiting 60s (ANTI-BAN)...")
                await asyncio.sleep(60) # ANTI-BAN: 60 seconds delay to prevent permanent API key ban
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return content.strip() if content else None
            raise Exception(f"Groq {model} error: {resp.status_code} — {resp.text[:200]}")

    async def _call_gemini(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Fallback: call Gemini API."""
        model = "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens}
            })
            if resp.status_code == 200:
                data = resp.json()
                content = data['candidates'][0]['content']['parts'][0]['text']
                return content.strip() if content else None
            raise Exception(f"Gemini error: {resp.status_code}")

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text that may contain markdown code fences."""
        # Try to find JSON in code fences first
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Try to find JSON object or array directly
        for pattern in [r'\{.*\}', r'\[.*\]']:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(0)
        return text.strip()

    @staticmethod
    def _cosine_similarity_score(title: str, description: str) -> dict:
        """Advanced vector-based scoring using TF-IDF and Cosine Similarity."""
        try:
            candidate_text = " ".join(
                [CANDIDATE_PROFILE['title']] +
                CANDIDATE_PROFILE['core_skills'] +
                CANDIDATE_PROFILE['protocols'] +
                CANDIDATE_PROFILE['security'] +
                CANDIDATE_PROFILE['cloud'] +
                CANDIDATE_PROFILE['automation'] +
                CANDIDATE_PROFILE['monitoring'] +
                CANDIDATE_PROFILE['infrastructure'] +
                CANDIDATE_PROFILE['certs']
            ).lower()
            job_text = (title + " " + description).lower()
            
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([candidate_text, job_text])
            
            # Compute cosine similarity between candidate and job
            cos_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Map 0-1 similarity to 0-100 score, shifted slightly higher
            score = int(min(100, cos_sim * 150))
            
            # Check for banned titles
            for banned in config.BANNED_TITLES:
                if banned.lower() in title.lower():
                    score = max(0, score - 60)
                    break
                    
            matching = [s for s in config.SKILLS if s.lower() in job_text]
            return {
                "score": score,
                "skills_match": matching[:15],
                "missing_skills": [],
                "experience_fit": "engineer" in job_text or "manager" in job_text or "architect" in job_text or "director" in job_text or "vp" in job_text or "cto" in job_text,
                "domain_fit": any(kw in job_text for kw in ["network", "infrastructure", "security", "cloud", "automation", "data center", "it"]),
                "recommendation": "apply" if score >= 65 else ("maybe" if score >= 45 else "skip"),
                "reason": f"Vector Cosine Similarity: {cos_sim:.2f}"
            }
        except Exception as e:
            logger.warning(f"Cosine similarity failed, falling back to keyword math: {e}")
            return AITailor._fallback_score(title, description)

    @staticmethod
    def _fallback_score(title: str, description: str) -> dict:
        """Simple keyword-based scoring fallback when AI and Cosine Similarity are unavailable."""
        text = (title + " " + description).lower()
        match_count = sum(1 for skill in config.SKILLS if skill.lower() in text)
        total_skills = len(config.SKILLS)
        score = min(100, int((match_count / max(total_skills * 0.1, 1)) * 60 + 20))

        # Check for banned titles
        for banned in config.BANNED_TITLES:
            if banned.lower() in title.lower():
                score = max(0, score - 60)
                break

        matching = [s for s in config.SKILLS if s.lower() in text]
        return {
            "score": score,
            "skills_match": matching[:15],
            "missing_skills": [],
            "experience_fit": "engineer" in text or "administrator" in text or "manager" in text or "architect" in text or "director" in text or "vp" in text or "cto" in text,
            "domain_fit": any(kw in text for kw in ["network", "infrastructure", "security", "cloud", "automation", "data center", "it ", "system", "devops", "sre"]),
            "recommendation": "apply" if score >= 65 else ("maybe" if score >= 45 else "skip"),
            "reason": f"Keyword-based score: {match_count} skills matched"
        }


# ── Singleton instance ──────────────────────────────────────────────────────
ai_tailor = AITailor()
