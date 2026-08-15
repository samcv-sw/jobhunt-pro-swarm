"""
ML Job Matcher: Machine learning-based job ranking
Learns from user's: applications, interviews, rejections, conversions
Trains XGBoost model to predict best-fit opportunities
Target: 60% fewer irrelevant applications
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime

from pydantic import BaseModel
import xgboost as xgb
from sklearn.preprocessing import StandardScaler


@dataclass
class JobMatchingFeatures:
    """Features for ML matching model"""
    job_title_similarity: float  # TF-IDF cosine similarity
    company_size_match: float  # 0-1
    salary_compatibility: float  # 0-1
    required_experience_match: float  # 0-1
    skill_overlap_score: float  # 0-1 (how many required skills user has)
    industry_experience: float  # 0-1 (years in this industry)
    location_preference_match: float  # 0-1
    growth_potential_score: float  # 0-1 (based on company research)
    user_interview_rate_similar_roles: float  # 0-1 (historical interview rate)
    company_health_score: float  # 0-100 (normalized to 0-1)
    glassdoor_rating_normalized: float  # 0-1
    days_since_posting: int
    
    def to_feature_vector(self) -> np.ndarray:
        """Convert to ML feature vector"""
        return np.array([
            self.job_title_similarity,
            self.company_size_match,
            self.salary_compatibility,
            self.required_experience_match,
            self.skill_overlap_score,
            self.industry_experience,
            self.location_preference_match,
            self.growth_potential_score,
            self.user_interview_rate_similar_roles,
            self.company_health_score / 100,  # Normalize to 0-1
            self.glassdoor_rating_normalized,
            min(self.days_since_posting / 30, 1.0),  # Normalize (0-1 for 30+ days)
        ])


class JobMatchingResult(BaseModel):
    """Prediction result from ML model"""
    job_id: str
    job_title: str
    company_name: str
    match_score: float  # 0-1
    predicted_interview_prob: float  # 0-1
    predicted_offer_prob: float  # 0-1
    top_matching_factors: List[str]  # Why this is a good match
    risk_factors: List[str]  # Potential issues
    recommendation: str  # "highly_recommend", "consider", "skip"


class MLJobMatcher:
    """
    ML-powered job matching
    - Trains on user's historical application data
    - Learns what types of jobs lead to interviews/offers
    - Ranks new jobs by predicted fit
    - Continuously improves with feedback
    """

    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "job_title_similarity",
            "company_size_match",
            "salary_compatibility",
            "required_experience_match",
            "skill_overlap_score",
            "industry_experience",
            "location_preference_match",
            "growth_potential_score",
            "user_interview_rate_similar_roles",
            "company_health_score",
            "glassdoor_rating_normalized",
            "days_since_posting",
        ]
        self.is_trained = False

    async def train_model(
        self,
        user_id: str,
        training_data: List[Dict]  # Historical applications with outcomes
    ) -> Dict[str, float]:
        """
        Train XGBoost model on user's historical data
        
        Args:
            user_id: User identifier
            training_data: [
                {
                    "job_id": "...",
                    "features": JobMatchingFeatures,
                    "outcome": "applied" | "interviewed" | "rejected" | "offered"
                }
            ]
            
        Returns:
            Model performance metrics
        """
        if len(training_data) < 10:
            return {"error": "Need at least 10 historical applications to train"}

        # Prepare data
        X = np.array([item["features"].to_feature_vector() for item in training_data])
        # Convert outcomes to binary (good fit = interviewed/offered, bad fit = rejected/no response)
        y = np.array([
            1 if item["outcome"] in ["interviewed", "offered"] else 0
            for item in training_data
        ])

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X_scaled, y, verbose=False)
        self.is_trained = True

        # Calculate performance metrics
        train_score = self.model.score(X_scaled, y)
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

        return {
            "accuracy": train_score,
            "total_samples": len(training_data),
            "feature_importance": feature_importance,
            "top_features": sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    async def predict_match(
        self,
        job_id: str,
        features: JobMatchingFeatures,
        job_title: str,
        company_name: str
    ) -> JobMatchingResult:
        """
        Predict match score for a job
        
        Args:
            job_id: Job identifier
            features: Extracted features for the job
            job_title: Job title for context
            company_name: Company name for context
            
        Returns:
            Prediction result with recommendation
        """
        if not self.is_trained:
            # Return baseline prediction if not trained
            return self._baseline_prediction(job_id, features, job_title, company_name)

        # Convert to feature vector
        X = features.to_feature_vector().reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        # Predict interview & offer probability
        interview_prob = float(self.model.predict_proba(X_scaled)[0][1])
        
        # Estimate offer probability (assume 50% of interviews convert to offers)
        offer_prob = interview_prob * 0.5

        # Generate recommendation
        if interview_prob > 0.75:
            recommendation = "highly_recommend"
        elif interview_prob > 0.50:
            recommendation = "consider"
        else:
            recommendation = "skip"

        # Extract top matching factors
        top_matching = self._extract_top_features(features, interview_prob)
        
        # Identify risk factors
        risk_factors = self._identify_risks(features, company_name)

        return JobMatchingResult(
            job_id=job_id,
            job_title=job_title,
            company_name=company_name,
            match_score=interview_prob,
            predicted_interview_prob=interview_prob,
            predicted_offer_prob=offer_prob,
            top_matching_factors=top_matching,
            risk_factors=risk_factors,
            recommendation=recommendation
        )

    def _baseline_prediction(
        self,
        job_id: str,
        features: JobMatchingFeatures,
        job_title: str,
        company_name: str
    ) -> JobMatchingResult:
        """Fallback prediction when model not trained"""
        # Simple weighted average
        base_score = (
            features.skill_overlap_score * 0.30 +
            features.salary_compatibility * 0.25 +
            features.job_title_similarity * 0.20 +
            features.company_health_score / 100 * 0.15 +
            features.location_preference_match * 0.10
        )

        recommendation = (
            "highly_recommend" if base_score > 0.75 else
            "consider" if base_score > 0.50 else
            "skip"
        )

        return JobMatchingResult(
            job_id=job_id,
            job_title=job_title,
            company_name=company_name,
            match_score=base_score,
            predicted_interview_prob=base_score,
            predicted_offer_prob=base_score * 0.5,
            top_matching_factors=["Strong skill match", "Good salary alignment"],
            risk_factors=[],
            recommendation=recommendation
        )

    def _extract_top_features(self, features: JobMatchingFeatures, score: float) -> List[str]:
        """Extract top 3 reasons for match"""
        reasons = []
        
        if features.skill_overlap_score > 0.8:
            reasons.append("Strong skill match")
        if features.salary_compatibility > 0.8:
            reasons.append("Good salary alignment")
        if features.company_health_score > 75:
            reasons.append("Healthy company financials")
        if features.job_title_similarity > 0.8:
            reasons.append("Perfect role title match")
        if features.growth_potential_score > 0.7:
            reasons.append("High growth potential")
        
        return reasons[:3] if reasons else ["Good overall fit"]

    def _identify_risks(self, features: JobMatchingFeatures, company_name: str) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        
        if features.skill_overlap_score < 0.6:
            risks.append("Missing some required skills")
        if features.salary_compatibility < 0.6:
            risks.append("Salary may be below market")
        if features.company_health_score < 50:
            risks.append("Company has financial concerns")
        if features.glassdoor_rating_normalized < 0.6:
            risks.append("Below-average company reviews")
        if features.required_experience_match < 0.6:
            risks.append("May lack sufficient experience")
        
        return risks


# Global instance
ml_job_matcher = MLJobMatcher()
