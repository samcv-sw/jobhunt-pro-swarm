import logging

from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)


class CheatSheetEngine:
    async def generate_cheat_sheet(self, company_name: str, job_title: str) -> str:
        """
        God Mode Feature: Generates a 1-page highly tailored tech interview
        cheat sheet specifically for the target company.
        """
        prompt = f"""
        You are an elite Tech Interview Coach.
        The user has an upcoming interview for a '{job_title}' role at '{company_name}'.
        
        Generate a concise, 1-page "Cheat Sheet" that includes:
        1. The likely Tech Stack {company_name} uses.
        2. Top 3 Technical Questions they will definitely ask.
        3. Top 3 Behavioral Questions (Amazon Leadership Principles style).
        4. "The Silver Bullet": One highly specific, impressive question the user should ask the interviewer at the end to blow their mind.
        
        Format it in Markdown, keep it extremely brief and high-impact.
        """

        # Use Semantic Cached AI call
        logger.info(f"Generating Cheat Sheet for {job_title} at {company_name}...")
        cheat_sheet = await ai_tailor._call_ai(prompt, max_tokens=600, temperature=0.7)

        if not cheat_sheet:
            return "Error: Could not generate cheat sheet."

        return cheat_sheet


# Singleton instance
cheat_sheet_engine = CheatSheetEngine()
