import logging
import json
import re
from typing import Dict, Any, List
from core.ai_tailor import ai_tailor
from core.ats_scorer import score_resume

logger = logging.getLogger(__name__)

class AgenticTailor:
    """
    AgenticTailor manages an iterative self-critiquing loop to optimize cover letters.
    It repeatedly calls the Generator (ai_tailor) and evaluates using the ATS Auditor (ats_scorer)
    until a threshold score (>90%) is achieved or max iterations are reached.
    """

    def __init__(self, target_score: int = 90, max_iterations: int = 3):
        self.target_score = target_score
        self.max_iterations = max_iterations

    async def generate_optimized_cover_letter(
        self,
        cv_text: str,
        job_description: str,
        job_title: str = "",
        user_id: str = None,
        company: str = None,
        regional_tone: str = "standard"
    ) -> Dict[str, Any]:
        """
        Iteratively generates and refines a cover letter using feedback from the ATS Scorer.
        Supports regional corporate tones: 'gulf_saudi_formal', 'uae_dubai_high_impact', 'global_remote_direct'.
        Returns a dict conforming to {"subject": "...", "body": "..."}.
        """
        logger.info(f"Starting Agentic ATS Self-Critiquing loop with tone: {regional_tone}...")
        
        tone_instructions = ""
        if regional_tone == "gulf_saudi_formal":
            tone_instructions = (
                "\nRegional Tone Directive: Tailor specifically for the Saudi Arabia & Gulf executive market. "
                "Use respectful, dignified phrasing, emphasizing loyalty, strategic value, leadership, and alignment with modern regional growth (Vision 2030)."
            )
        elif regional_tone == "uae_dubai_high_impact":
            tone_instructions = (
                "\nRegional Tone Directive: Tailor for the fast-paced UAE/Dubai corporate ecosystem. "
                "Keep sentences punchy, lead with quantified ROI/KPI achievements, and showcase high-energy commercial drive."
            )
        elif regional_tone == "global_remote_direct":
            tone_instructions = (
                "\nRegional Tone Directive: High-impact global remote style. Focus on asynchronous autonomy, direct problem solving, and zero fluff."
            )

        # Initial prompt to generate the cover letter in JSON format
        system_prompt = f"""You are an expert executive recruiter and copywriter. Write a persuasive, concise cover letter.{tone_instructions}
        Output valid JSON ONLY with this exact schema:
        {{
            "subject": "Compelling subject line for the email",
            "body": "The full text of the cover letter, using proper paragraph breaks (\\n\\n)"
        }}"""

        user_prompt = f"""
        Job Description:
        {job_description}

        User CV:
        {cv_text}
        """
        
        current_data = {"subject": "", "body": ""}
        history = []

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"Agentic Loop Iteration {iteration}/{self.max_iterations}")
            
            # Step 1: Generate or refine cover letter
            response = await ai_tailor._call_ai(user_prompt if iteration > 1 else f"{system_prompt}\n\n{user_prompt}", max_tokens=1024, temperature=0.5)
            if not response:
                logger.error("AI Generation returned empty response.")
                if current_data["body"]:
                    break
                return {"status": "error", "message": "Failed to generate cover letter"}
            
            try:
                # Clean/Extract JSON and parse it
                json_str = ai_tailor._extract_json(response)
                parsed_response = json.loads(json_str)
                if isinstance(parsed_response, dict) and "body" in parsed_response:
                    current_data = parsed_response
            except Exception as parse_err:
                logger.warning(f"Failed to parse cover letter JSON: {parse_err}")
                # Fallback extraction if parsing fails but text exists
                if not current_data["body"]:
                    current_data = {
                        "subject": f"Application for {job_title or 'Position'}",
                        "body": response
                    }

            # Step 2: Score current version using ATS Auditor
            logger.info("Auditing cover letter with ATS Scorer...")
            audit_result = await score_resume(
                resume_text=current_data["body"],
                job_description=job_description,
                job_title=job_title
            )
            
            score = audit_result.get("overall_score", 0)
            logger.info(f"Iteration {iteration} Audit Score: {score}/100")
            
            history.append({
                "iteration": iteration,
                "score": score,
                "missing_keywords": audit_result.get("missing_keywords", []),
                "suggestions": audit_result.get("suggestions", [])
            })
            
            # Step 3: Check if target score is reached
            if score >= self.target_score:
                logger.info(f"Target score of {self.target_score} achieved! Ending loop.")
                break
            
            # Step 4: Construct critique prompt for refinement
            missing_kws = ", ".join(audit_result.get("missing_keywords", []))
            suggestions = "\n- ".join(audit_result.get("suggestions", []))
            
            user_prompt = f"""
            You previously generated this cover letter JSON:
            {json.dumps(current_data)}
            
            The ATS Auditor scored the letter body {score}/100 and provided the following critique:
            
            Missing Keywords to integrate naturally:
            {missing_kws if missing_kws else "None"}
            
            Suggestions for improvement:
            - {suggestions if suggestions else "Enhance overall alignment"}
            
            Please rewrite the cover letter body, implementing all suggestions and naturally incorporating the missing keywords to improve the ATS match.
            You MUST output valid JSON ONLY, adhering exactly to the schema:
            {{
                "subject": "Compelling subject line for the email",
                "body": "The full text of the cover letter, using proper paragraph breaks (\\n\\n)"
            }}
            
            Original CV for reference:
            {cv_text[:1500]}
            
            Original Job Description for reference:
            {job_description[:1500]}
            """

        # Return standard response fields with audit trace injected if needed
        return current_data
