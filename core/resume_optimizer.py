"""
ATS Resume Optimizer — Groq-powered keyword extraction & resume tailoring
Integrates with LLMProviderPool for multi-provider AI + direct Groq fallback.

Generates optimized resume sections tailored to a specific job description,
extracting critical keywords and restructuring candidate content to maximize
ATS match scores while remaining readable for human reviewers.

Usage:
    optimizer = ResumeOptimizer()
    # Extract keywords from a job description
    keywords = optimizer.parse_job_keywords(job_description)
    # Optimize resume text against JD keywords
    result = optimizer.generate_ats_resume(cv_path, job_description)

Supports fields: target_job_title, target_company, extracted_keywords, optimized_sections
"""

import json
import os
import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import config

logger = logging.getLogger(__name__)

# ── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class OptimizedSection:
    """A single optimized section of the resume."""
    section_name: str       # e.g. "Professional Summary", "Technical Skills"
    original_text: str      # Original content before optimization
    optimized_text: str     # Keyword-enriched optimized content
    injected_keywords: List[str] = field(default_factory=list)  # Keywords added to this section

@dataclass
class ATSOptimizationResult:
    """Full result of the ATS resume optimization pipeline."""
    target_job_title: str = ""
    target_company: str = ""
    extracted_keywords: List[str] = field(default_factory=list)
    keyword_categories: Dict[str, List[str]] = field(default_factory=dict)
    optimized_sections: List[OptimizedSection] = field(default_factory=list)
    optimized_full_text: str = ""
    match_score_estimate: int = 0
    missing_skills: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to a flat dict suitable for DB storage or JSON serialization."""
        return {
            "target_job_title": self.target_job_title,
            "target_company": self.target_company,
            "extracted_keywords": json.dumps(self.extracted_keywords, ensure_ascii=False),
            "optimized_sections": json.dumps(
                [asdict(s) for s in self.optimized_sections],
                ensure_ascii=False,
            ),
            "match_score_estimate": self.match_score_estimate,
            "missing_skills": json.dumps(self.missing_skills, ensure_ascii=False),
            "suggestions": json.dumps(self.suggestions, ensure_ascii=False),
        }


# ── System Prompts ──────────────────────────────────────────────────────────

SYSTEM_KEYWORD_EXTRACTOR = """You are an expert ATS keyword extraction specialist. Your job is to analyze a job description and extract ALL critical keywords, skills, certifications, tools, and technologies mentioned.

Rules:
1. Extract ALL technical skills (languages, frameworks, tools, platforms)
2. Extract ALL soft skills mentioned
3. Extract ALL certifications and qualifications
4. Extract ALL domain-specific terminology
5. Categorize keywords into: technical_skills, soft_skills, certifications, tools, domain_knowledge
6. Be exhaustive — missing a keyword costs the candidate a lower ATS score
7. Return ONLY valid JSON, no markdown, no code fences

Return format:
{
  "technical_skills": ["Cisco", "BGP", "OSPF"],
  "soft_skills": ["leadership", "communication"],
  "certifications": ["CCNA", "CCNP"],
  "tools": ["Wireshark", "PRTG"],
  "domain_knowledge": ["MPLS", "VPN"],
  "all_keywords": ["Cisco", "BGP", "OSPF", "leadership", ...]
}"""

SYSTEM_RESUME_OPTIMIZER = """You are an expert ATS resume optimizer. Your job is to rewrite sections of a candidate's resume to maximize match with specific keywords from a job description.

Rules:
1. Preserve the candidate's actual experience — NEVER fabricate skills, certifications, or experience
2. Naturally weave the target keywords into existing content where contextually appropriate
3. Rephrase bullet points to use exact phrasing from the JD (e.g., "led team" → "led cross-functional team" if JD says that)
4. Prioritize keywords that appear multiple times in the job description
5. Keep all content truthful, factual, and verifiable
6. Maintain professional tone and readability
7. For each section, track which keywords you injected
8. Return ONLY valid JSON — no markdown, no code fences

Return format:
{
  "sections": [
    {
      "section_name": "Professional Summary",
      "optimized_text": "Senior Network Engineer with 15+ years...",
      "injected_keywords": ["keyword1", "keyword2"]
    }
  ],
  "missing_skills": ["skill still absent from resume"],
  "suggestions": ["Consider adding X certification"],
  "estimated_match_score": 85
}"""


# ── Resume Optimizer ────────────────────────────────────────────────────────

class ResumeOptimizer:
    """AI-powered ATS resume optimizer using LLM provider pool + direct Groq fallback."""

    def __init__(self, llm_pool=None):
        """
        Args:
            llm_pool: Optional LLMProviderPool instance for multi-provider AI.
                      If None, uses direct Groq AsyncClient.
        """
        self._llm_pool = llm_pool
        self._groq_keys = self._load_groq_keys()

    # ── Groq Key Loader ────────────────────────────────────────────────────

    @staticmethod
    def _load_groq_keys() -> List[str]:
        """Load Groq API keys from env variables with rotation support."""
        primary = os.getenv("GROQ_PRIMARY_KEY") or os.getenv("GROQ_API_KEY") or ""
        rotation = os.getenv("GROQ_ROTATION_KEYS", "")
        if rotation:
            keys = [k.strip() for k in rotation.split(",") if k.strip()]
        else:
            keys = [primary] if primary else []
        # Hardcoded fallback key
        if not keys:
            keys = [os.getenv("GROQ_API_KEY", "")]
        return keys

    # ── Core AI Call ───────────────────────────────────────────────────────

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        prefer_groq: bool = False,
    ) -> Optional[str]:
        """Call LLM via provider pool (preferred) or direct Groq fallback.

        Uses the LLMProviderPool when available for multi-provider rotation.
        Falls back to direct Groq AsyncClient when pool is not configured.
        """
        # Try provider pool first
        if self._llm_pool:
            try:
                from core.llm_provider_pool import LLMProvider
                preferred = LLMProvider.GROQ if prefer_groq else None
                result = await self._llm_pool.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    preferred_provider=preferred,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if result:
                    return result.strip()
            except Exception as e:
                logger.warning(f"LLM pool call failed: {e}, falling back to direct Groq")

        # Fallback: direct Groq AsyncClient
        if not self._groq_keys:
            logger.error("No Groq API keys available")
            return None

        from groq import AsyncGroq

        for key in self._groq_keys:
            try:
                client = AsyncGroq(api_key=key)
                resp = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content
                if content and content.strip():
                    return content.strip()
            except Exception as e:
                logger.warning(f"Groq key failed: {e}, trying next key")
                continue

        logger.error("All Groq keys exhausted")
        return None

    # ── Parse Job Keywords ─────────────────────────────────────────────────

    async def parse_job_keywords(self, job_description: str, job_title: str = "") -> Dict[str, List[str]]:
        """Extract categorized keywords from a job description using AI.

        Args:
            job_description: Full text of the job posting
            job_title: Optional job title for extra context

        Returns:
            Dict with keys: technical_skills, soft_skills, certifications, tools,
                           domain_knowledge, all_keywords
        """
        user_prompt = f"Job Title: {job_title or 'N/A'}\n\nJob Description:\n{job_description[:5000]}"

        raw = await self._call_llm(
            system_prompt=SYSTEM_KEYWORD_EXTRACTOR,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=1024,
        )

        if not raw:
            logger.warning("Keyword extraction returned empty, using fallback")
            return self._fallback_extract_keywords(job_description)

        # Clean markdown code fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            result = json.loads(raw)
            # Ensure all categories exist
            categories = ["technical_skills", "soft_skills", "certifications", "tools", "domain_knowledge"]
            for cat in categories:
                if cat not in result or not isinstance(result[cat], list):
                    result[cat] = []
            if "all_keywords" not in result or not isinstance(result["all_keywords"], list):
                # Build merged deduplicated list
                seen = set()
                all_kw = []
                for cat in categories:
                    for kw in result.get(cat, []):
                        kw_norm = kw.strip().lower()
                        if kw_norm and kw_norm not in seen:
                            seen.add(kw_norm)
                            all_kw.append(kw.strip())
                result["all_keywords"] = all_kw
            return result
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse keyword JSON: {e}, raw={raw[:200]}")
            return self._fallback_extract_keywords(job_description)

    def parse_job_keywords_sync(self, job_description: str, job_title: str = "") -> Dict[str, List[str]]:
        """Synchronous wrapper for parse_job_keywords."""
        return asyncio.run(self.parse_job_keywords(job_description, job_title))

    # ── Fallback Keyword Extraction ───────────────────────────────────────

    def _fallback_extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Rule-based fallback keyword extraction when AI fails.
        Uses config.SKILLS and common patterns to extract keywords."""
        text_lower = text.lower()
        found_skills = []
        found_certs = []
        found_tools = []
        found_domain = []

        # Match against known skills from config
        for skill in config.SKILLS:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        # Match certifications
        cert_patterns = [
            r'\b(ccna|ccnp|ccie|comptia|nse|mtcna|mtcre)\b',
            r'\b(certified|certification)\s+\w+',
            r'\b(pmp|itil|aws\s+solutions|azure\s+administrator)\b',
        ]
        for pattern in cert_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                found_certs.append(match.group(0))

        # Match tools
        tool_patterns = [
            r'\b(wireshark|prtg|nagios|zabbix|solarwinds|ansible|terraform)\b',
            r'\b(docker|kubernetes|jenkins|gitlab|jira|confluence)\b',
        ]
        for pattern in tool_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                found_tools.append(match.group(0))

        # Match domain knowledge
        domain_patterns = [
            r'\b(ospf|bgp|mpls|vlan|vxlan|sdn|nfv|vpn|ipsec|ssl)\b',
            r'\b(firewall|load\s*balancer|proxy|vpc|nat|acl)\b',
        ]
        for pattern in domain_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                found_domain.append(match.group(0))

        # Deduplicate
        found_skills = list(dict.fromkeys(found_skills))
        found_certs = list(dict.fromkeys(found_certs))
        found_tools = list(dict.fromkeys(found_tools))
        found_domain = list(dict.fromkeys(found_domain))

        all_keywords = found_skills + found_certs + found_tools + found_domain
        all_keywords = list(dict.fromkeys(all_keywords))

        return {
            "technical_skills": found_skills,
            "soft_skills": [],
            "certifications": found_certs,
            "tools": found_tools,
            "domain_knowledge": found_domain,
            "all_keywords": all_keywords,
        }

    # ── Optimize Resume Sections ──────────────────────────────────────────

    async def optimize_resume_sections(
        self,
        cv_text: str,
        keywords: Dict[str, List[str]],
        sections_to_optimize: Optional[List[str]] = None,
        job_title: str = "",
        company: str = "",
    ) -> ATSOptimizationResult:
        """Rewrite resume sections for maximum ATS keyword match.

        Args:
            cv_text: Full text of the candidate's resume
            keywords: Dict of categorized keywords (from parse_job_keywords)
            sections_to_optimize: List of sections to optimize, e.g.
                ["Professional Summary", "Technical Skills", "Experience"]
                If None, attempts to detect sections from CV text.
            job_title: Target job title
            company: Target company name

        Returns:
            ATSOptimizationResult with optimized sections and full text
        """
        all_keywords = keywords.get("all_keywords", [])
        keyword_summary = json.dumps(keywords, ensure_ascii=False, indent=2)

        user_prompt = f"""Job Title: {job_title or 'N/A'}
Target Company: {company or 'N/A'}

Keywords to inject (categorized):
{keyword_summary[:2000]}

Candidate Resume:
{cv_text[:5000]}

Sections to optimize: {sections_to_optimize or 'Auto-detect from resume'}

Rewrite each section naturally incorporating the target keywords.
Preserve all factual experience — do NOT fabricate.
Track which keywords were injected per section."""

        raw = await self._call_llm(
            system_prompt=SYSTEM_RESUME_OPTIMIZER,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=3072,
        )

        if not raw:
            logger.warning("Resume optimization returned empty, returning original CV")
            return self._fallback_optimize(cv_text, keywords, job_title, company)

        # Clean JSON
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse optimization JSON: {e}, returning fallback")
            return self._fallback_optimize(cv_text, keywords, job_title, company)

        # Build result
        result = ATSOptimizationResult(
            target_job_title=job_title,
            target_company=company,
            extracted_keywords=all_keywords,
            keyword_categories=keywords,
        )

        # Parse sections
        raw_sections = data.get("sections", [])
        optimized_parts = []
        for sec in raw_sections:
            if not isinstance(sec, dict):
                continue
            section_name = sec.get("section_name", "Unknown")
            optimized_text = sec.get("optimized_text", "")
            injected = sec.get("injected_keywords", [])

            if not optimized_text:
                continue

            section = OptimizedSection(
                section_name=section_name,
                original_text="",
                optimized_text=optimized_text,
                injected_keywords=injected if isinstance(injected, list) else [],
            )
            result.optimized_sections.append(section)
            optimized_parts.append(f"## {section_name}\n{optimized_text}")

        # Build full text
        if optimized_parts:
            result.optimized_full_text = "\n\n".join(optimized_parts)
        else:
            result.optimized_full_text = cv_text

        # Metadata
        result.missing_skills = data.get("missing_skills", [])
        if not isinstance(result.missing_skills, list):
            result.missing_skills = []
        result.suggestions = data.get("suggestions", [])
        if not isinstance(result.suggestions, list):
            result.suggestions = []
        result.match_score_estimate = min(100, max(0, int(data.get("estimated_match_score", 0))))

        logger.info(
            f"Resume optimized for '{job_title}' at '{company}': "
            f"{len(result.optimized_sections)} sections, "
            f"{len(all_keywords)} keywords, "
            f"estimated match {result.match_score_estimate}%"
        )
        return result

    def optimize_resume_sections_sync(
        self,
        cv_text: str,
        keywords: Dict[str, List[str]],
        sections_to_optimize: Optional[List[str]] = None,
        job_title: str = "",
        company: str = "",
    ) -> ATSOptimizationResult:
        """Synchronous wrapper for optimize_resume_sections."""
        return asyncio.run(self.optimize_resume_sections(
            cv_text, keywords, sections_to_optimize, job_title, company
        ))

    # ── Fallback Optimize ──────────────────────────────────────────────────

    def _fallback_optimize(
        self,
        cv_text: str,
        keywords: Dict[str, List[str]],
        job_title: str = "",
        company: str = "",
    ) -> ATSOptimizationResult:
        """Rule-based fallback when AI optimization fails.
        Injects keywords into a professional summary section."""
        all_keywords = keywords.get("all_keywords", [])
        # Take top 10 most relevant keywords from config.SKILLS
        top_kw = [kw for kw in all_keywords if kw.lower() in config.SKILLS][:10]

        summary = (
            f"Senior Network Engineer with 15+ years of experience in "
            f"{', '.join(top_kw[:5]) if top_kw else 'enterprise networking'}."
        )

        section = OptimizedSection(
            section_name="Professional Summary",
            original_text="",
            optimized_text=summary,
            injected_keywords=top_kw,
        )

        result = ATSOptimizationResult(
            target_job_title=job_title,
            target_company=company,
            extracted_keywords=all_keywords,
            keyword_categories=keywords,
            optimized_sections=[section],
            optimized_full_text=summary,
            match_score_estimate=40,
            missing_skills=all_keywords[10:] if len(all_keywords) > 10 else [],
            suggestions=["Use AI optimization for better results"],
        )
        return result

    # ── Full Pipeline: Generate ATS Resume ────────────────────────────────

    async def generate_ats_resume(
        self,
        cv_path: Optional[str] = None,
        cv_text: Optional[str] = None,
        job_description: str = "",
        output_path: Optional[str] = None,
        job_title: str = "",
        company: str = "",
    ) -> ATSOptimizationResult:
        """End-to-end ATS resume generation pipeline.

        1. Load CV text (from file or provided directly)
        2. Extract keywords from job description
        3. Optimize resume sections against keywords
        4. Optionally save optimized result to file

        Args:
            cv_path: Path to the CV file (PDF or TXT). If None, use cv_text.
            cv_text: Raw CV text (alternative to cv_path).
            job_description: Full text of the target job posting.
            output_path: Optional path to save the optimized text.
            job_title: Target job title.
            company: Target company name.

        Returns:
            ATSOptimizationResult with all optimized data.
        """
        # Step 1: Load CV text
        if not cv_text:
            if not cv_path:
                cv_path = config.CV_PATH
            cv_text = await self._load_cv_text(cv_path)

        if not cv_text:
            raise ValueError("No CV text available — provide cv_text or a valid cv_path")

        # Step 2: Parse job keywords
        logger.info(f"Parsing keywords from job description...")
        keywords = await self.parse_job_keywords(job_description, job_title)
        kw_count = len(keywords.get("all_keywords", []))
        logger.info(f"Extracted {kw_count} keywords across "
                     f"{sum(1 for v in keywords.values() if isinstance(v, list))} categories")

        # Step 3: Optimize resume sections
        logger.info(f"Optimizing resume for '{job_title}' at '{company}'...")
        result = await self.optimize_resume_sections(
            cv_text=cv_text,
            keywords=keywords,
            job_title=job_title,
            company=company,
        )

        # Step 4: Save to file if requested
        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.optimized_full_text)
            logger.info(f"Optimized resume saved to {output_path}")

        return result

    def generate_ats_resume_sync(
        self,
        cv_path: Optional[str] = None,
        cv_text: Optional[str] = None,
        job_description: str = "",
        output_path: Optional[str] = None,
        job_title: str = "",
        company: str = "",
    ) -> ATSOptimizationResult:
        """Synchronous wrapper for generate_ats_resume."""
        return asyncio.run(self.generate_ats_resume(
            cv_path=cv_path,
            cv_text=cv_text,
            job_description=job_description,
            output_path=output_path,
            job_title=job_title,
            company=company,
        ))

    # ── CV Text Loader ─────────────────────────────────────────────────────

    @staticmethod
    async def _load_cv_text(cv_path: Optional[str] = None) -> str:
        """Load CV text from PDF or plain text file."""
        if not cv_path:
            cv_path = config.CV_PATH

        if not cv_path or not os.path.exists(cv_path):
            logger.warning(f"CV file not found at {cv_path}")
            return ""

        ext = os.path.splitext(cv_path)[1].lower()

        if ext in (".txt", ".md", ".rtf"):
            with open(cv_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

        elif ext == ".pdf":
            try:
                import pdfplumber
            except ImportError:
                try:
                    import PyPDF2
                    with open(cv_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    return text
                except ImportError:
                    pass
                try:
                    import pdfminer
                    # pdfminer approach
                    pass
                except ImportError:
                    logger.warning("No PDF reader available (install pdfplumber or PyPDF2)")
                    return ""

            # pdfplumber is preferred
            try:
                import pdfplumber
                with pdfplumber.open(cv_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"pdfplumber failed on {cv_path}: {e}")

            # Fallback to PyPDF2
            try:
                import PyPDF2
                with open(cv_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text
            except Exception as e:
                logger.warning(f"PyPDF2 fallback failed: {e}")

        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(cv_path)
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                logger.warning("python-docx not installed for .docx files")
                return ""
            except Exception as e:
                logger.warning(f"Failed to read .docx: {e}")
                return ""

        else:
            logger.warning(f"Unsupported CV format: {ext}")
            return ""


# ── Standalone API ──────────────────────────────────────────────────────────

def parse_job_keywords(job_description: str, job_title: str = "") -> Dict[str, List[str]]:
    """Quick one-shot keyword extraction — no optimizer instance needed.

    Example:
        >>> keywords = parse_job_keywords(jd_text, "Network Engineer")
        >>> print(keywords["all_keywords"])
    """
    opt = ResumeOptimizer()
    return opt.parse_job_keywords_sync(job_description, job_title)


def optimize_resume(cv_text: str, job_description: str,
                    job_title: str = "", company: str = "") -> ATSOptimizationResult:
    """Quick one-shot resume optimization — no optimizer instance needed."""
    opt = ResumeOptimizer()
    keywords = opt.parse_job_keywords_sync(job_description, job_title)
    return opt.optimize_resume_sections_sync(cv_text, keywords, job_title=job_title, company=company)


def generate_ats_resume(cv_path: str, job_description: str,
                        output_path: Optional[str] = None,
                        job_title: str = "", company: str = "") -> ATSOptimizationResult:
    """Quick one-shot end-to-end ATS resume generation."""
    opt = ResumeOptimizer()
    return opt.generate_ats_resume_sync(
        cv_path=cv_path,
        job_description=job_description,
        output_path=output_path,
        job_title=job_title,
        company=company,
    )
