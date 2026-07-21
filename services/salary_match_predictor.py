"""
AI Salary Benchmark & Match Predictor Engine
Heuristic ML matching candidate skill density to job criteria and estimating salary benchmarks.
"""
from typing import Dict, Any, List
import re

class SalaryMatchPredictorEngine:
    """
    Predicts salary ranges and candidate-job compatibility score.
    """

    BASE_SALARIES = {
        "software engineer": {"junior": 60000, "mid": 95000, "senior": 145000, "lead": 180000},
        "data scientist": {"junior": 65000, "mid": 100000, "senior": 150000, "lead": 185000},
        "product manager": {"junior": 70000, "mid": 105000, "senior": 155000, "lead": 190000},
        "devops engineer": {"junior": 65000, "mid": 98000, "senior": 148000, "lead": 178000},
        "general": {"junior": 50000, "mid": 75000, "senior": 115000, "lead": 145000}
    }

    def predict_match_and_salary(self, candidate_skills: List[str], candidate_experience_years: int, job_role: str, required_skills: List[str]) -> Dict[str, Any]:
        """
        Calculates match score (0-100%) and predicts salary range.
        """
        # Skill matching
        cand_skills_set = {s.lower().strip() for s in candidate_skills}
        req_skills_set = {s.lower().strip() for s in required_skills}

        if not req_skills_set:
            match_score = 80.0
        else:
            intersection = cand_skills_set.intersection(req_skills_set)
            match_score = (len(intersection) / len(req_skills_set)) * 100.0

        # Adjust match score for experience
        if candidate_experience_years >= 5:
            match_score += 10.0
        elif candidate_experience_years >= 2:
            match_score += 5.0

        match_score = round(min(100.0, max(0.0, match_score)), 1)

        # Seniority level determination
        if candidate_experience_years >= 8:
            level = "lead"
        elif candidate_experience_years >= 5:
            level = "senior"
        elif candidate_experience_years >= 2:
            level = "mid"
        else:
            level = "junior"

        # Base salary determination
        role_key = job_role.lower().strip()
        role_salaries = self.BASE_SALARIES.get(role_key, self.BASE_SALARIES["general"])
        base_salary = role_salaries[level]

        # Skill bonus (5% per matching skill)
        skill_bonus = base_salary * (min(len(cand_skills_set), 10) * 0.02)
        predicted_min = int(base_salary + skill_bonus - 10000)
        predicted_max = int(base_salary + skill_bonus + 15000)
        median_expected = int((predicted_min + predicted_max) / 2)

        return {
            "match_score_pct": match_score,
            "seniority_level": level.capitalize(),
            "predicted_salary_min": predicted_min,
            "predicted_salary_max": predicted_max,
            "median_salary": median_expected,
            "currency": "USD",
            "matched_skills": list(cand_skills_set.intersection(req_skills_set)),
            "missing_skills": list(req_skills_set - cand_skills_set)
        }

salary_match_predictor = SalaryMatchPredictorEngine()
