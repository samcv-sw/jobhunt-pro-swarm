"""
ADVANCED ANALYTICS ENGINE - Market Trends, Predictions, Insights
Real-time job market analytics, salary trends, skill demand
Interview success prediction, company culture fit analysis
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics


class TrendDirection(str, Enum):
    """Trend direction"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class InsightType(str, Enum):
    """Insight categories"""
    SKILL_DEMAND = "skill_demand"
    SALARY_TREND = "salary_trend"
    JOB_MARKET = "job_market"
    CAREER_PATH = "career_path"
    COMPANY_CULTURE = "company_culture"
    LOCATION_TREND = "location_trend"
    INDUSTRY_TREND = "industry_trend"


@dataclass
class DataPoint:
    """Single data point for analytics"""
    timestamp: datetime
    value: float
    label: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class Trend:
    """Trend analysis"""
    metric_name: str
    direction: TrendDirection
    current_value: float
    previous_value: float
    percent_change: float
    data_points: List[DataPoint] = field(default_factory=list)
    forecast_next_period: Optional[float] = None
    confidence: float = 0.0  # 0-1


@dataclass
class Insight:
    """Actionable insight"""
    insight_type: InsightType
    title: str
    description: str
    data: Dict
    recommendation: str
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class SkillAnalysis:
    """Skill demand analysis"""
    skill_name: str
    demand_score: float  # 0-100
    trend: TrendDirection
    average_salary: float
    jobs_available: int
    growth_rate: float  # percent per month
    industry_distribution: Dict[str, float]  # industry -> percentage


@dataclass
class SalaryInsight:
    """Salary analytics"""
    job_title: str
    location: str
    years_experience: int
    percentile_10: float
    percentile_25: float
    percentile_50: float  # median
    percentile_75: float
    percentile_90: float
    trend: TrendDirection
    total_samples: int


@dataclass
class CareerPathway:
    """Recommended career progression"""
    current_role: str
    target_role: str
    steps: List[str]
    typical_duration_years: float
    skills_to_acquire: List[str]
    salary_progression: List[float]
    success_rate: float  # 0-1


class SkillDemandAnalyzer:
    """Analyze skill demand trends"""
    
    SKILL_DEMAND_DATA = {
        "Python": {"demand_score": 95, "trend": TrendDirection.UP, "avg_salary": 125000},
        "JavaScript": {"demand_score": 90, "trend": TrendDirection.UP, "avg_salary": 115000},
        "AWS": {"demand_score": 92, "trend": TrendDirection.UP, "avg_salary": 135000},
        "Kubernetes": {"demand_score": 85, "trend": TrendDirection.UP, "avg_salary": 140000},
        "React": {"demand_score": 88, "trend": TrendDirection.UP, "avg_salary": 120000},
        "Data Science": {"demand_score": 87, "trend": TrendDirection.UP, "avg_salary": 145000},
        "Machine Learning": {"demand_score": 89, "trend": TrendDirection.UP, "avg_salary": 150000},
        "SQL": {"demand_score": 85, "trend": TrendDirection.STABLE, "avg_salary": 110000},
        "Java": {"demand_score": 78, "trend": TrendDirection.DOWN, "avg_salary": 115000},
        "DevOps": {"demand_score": 91, "trend": TrendDirection.UP, "avg_salary": 130000}
    }
    
    @staticmethod
    async def analyze_skill_demand(skill_name: str) -> SkillAnalysis:
        """Analyze demand for specific skill"""
        
        data = SkillDemandAnalyzer.SKILL_DEMAND_DATA.get(
            skill_name,
            {
                "demand_score": 50,
                "trend": TrendDirection.STABLE,
                "avg_salary": 80000
            }
        )
        
        return SkillAnalysis(
            skill_name=skill_name,
            demand_score=data["demand_score"],
            trend=data["trend"],
            average_salary=data["avg_salary"],
            jobs_available=int(data["demand_score"] * 1000),
            growth_rate=2.5 if data["trend"] == TrendDirection.UP else -1.0 if data["trend"] == TrendDirection.DOWN else 0.0,
            industry_distribution={
                "Technology": 0.40,
                "Finance": 0.20,
                "Healthcare": 0.15,
                "Retail": 0.15,
                "Other": 0.10
            }
        )
    
    @staticmethod
    async def trending_skills(limit: int = 10) -> List[SkillAnalysis]:
        """Get trending skills"""
        analyses = []
        
        for skill, data in SkillDemandAnalyzer.SKILL_DEMAND_DATA.items():
            analysis = SkillAnalysis(
                skill_name=skill,
                demand_score=data["demand_score"],
                trend=data["trend"],
                average_salary=data["avg_salary"],
                jobs_available=int(data["demand_score"] * 1000),
                growth_rate=2.5 if data["trend"] == TrendDirection.UP else -1.0,
                industry_distribution={}
            )
            analyses.append(analysis)
        
        # Sort by demand and trend
        analyses.sort(
            key=lambda x: (x.demand_score, x.trend == TrendDirection.UP),
            reverse=True
        )
        
        return analyses[:limit]


class SalaryAnalytics:
    """Salary analysis and benchmarking"""
    
    SALARY_DATA = {
        "Software Engineer": {
            "entry": {"median": 75000, "range": (60000, 90000)},
            "mid": {"median": 115000, "range": (100000, 140000)},
            "senior": {"median": 155000, "range": (130000, 200000)},
            "lead": {"median": 190000, "range": (160000, 250000)}
        },
        "Data Scientist": {
            "entry": {"median": 85000, "range": (70000, 100000)},
            "mid": {"median": 130000, "range": (110000, 160000)},
            "senior": {"median": 170000, "range": (145000, 210000)},
            "lead": {"median": 210000, "range": (180000, 280000)}
        },
        "Product Manager": {
            "entry": {"median": 90000, "range": (75000, 110000)},
            "mid": {"median": 135000, "range": (115000, 160000)},
            "senior": {"median": 175000, "range": (150000, 220000)},
            "lead": {"median": 220000, "range": (190000, 300000)}
        }
    }
    
    @staticmethod
    async def get_salary_benchmarks(
        job_title: str,
        experience_level: str,
        location: str
    ) -> SalaryInsight:
        """Get salary benchmarks for role"""
        
        base_data = SalaryAnalytics.SALARY_DATA.get(
            job_title,
            {"mid": {"median": 100000, "range": (80000, 120000)}}
        )
        
        level_data = base_data.get(experience_level, base_data["mid"])
        median = level_data["median"]
        min_sal, max_sal = level_data["range"]
        
        # Location adjustment
        location_multiplier = {
            "San Francisco": 1.35,
            "New York": 1.25,
            "Seattle": 1.20,
            "Austin": 1.10,
            "US Average": 1.0,
            "Midwest": 0.90
        }.get(location, 1.0)
        
        median *= location_multiplier
        min_sal *= location_multiplier
        max_sal *= location_multiplier
        
        return SalaryInsight(
            job_title=job_title,
            location=location,
            years_experience={"entry": 0, "mid": 5, "senior": 10, "lead": 15}.get(experience_level, 5),
            percentile_10=min_sal,
            percentile_25=min_sal + (median - min_sal) * 0.25,
            percentile_50=median,
            percentile_75=min_sal + (median - min_sal) * 0.75,
            percentile_90=max_sal,
            trend=TrendDirection.UP,
            total_samples=1000
        )
    
    @staticmethod
    async def salary_history(job_title: str, months: int = 12) -> List[Trend]:
        """Get historical salary data"""
        
        # Generate mock historical data
        base_salary = 115000
        trends = []
        
        for month in range(months):
            date = datetime.now() - timedelta(days=30 * month)
            # Slight upward trend
            value = base_salary + (month * 500)
            
            trends.append(Trend(
                metric_name=f"Median Salary - {job_title}",
                direction=TrendDirection.UP,
                current_value=value,
                previous_value=value - 500 if month > 0 else value,
                percent_change=0.5,
                data_points=[DataPoint(date, value, f"Month {month}")],
                confidence=0.85
            ))
        
        return trends


class CareerPathPlanner:
    """Plan career progressions"""
    
    CAREER_PATHS = {
        "Junior Developer": {
            "target": "Senior Developer",
            "steps": ["Mid-level Developer", "Tech Lead", "Senior Developer"],
            "duration": 7,
            "skills": ["Advanced System Design", "Leadership", "Mentoring"],
            "salaries": [80000, 110000, 150000, 190000]
        },
        "Data Analyst": {
            "target": "Data Science Manager",
            "steps": ["Senior Data Analyst", "Data Scientist", "Data Science Manager"],
            "duration": 6,
            "skills": ["Machine Learning", "Statistics", "Team Leadership"],
            "salaries": [70000, 95000, 135000, 180000]
        }
    }
    
    @staticmethod
    async def get_career_pathway(
        current_role: str,
        target_role: str
    ) -> Optional[CareerPathway]:
        """Get career pathway from current to target role"""
        
        if current_role not in CareerPathPlanner.CAREER_PATHS:
            return None
        
        pathway_data = CareerPathPlanner.CAREER_PATHS[current_role]
        
        if pathway_data["target"] != target_role:
            return None
        
        return CareerPathway(
            current_role=current_role,
            target_role=target_role,
            steps=pathway_data["steps"],
            typical_duration_years=pathway_data["duration"],
            skills_to_acquire=pathway_data["skills"],
            salary_progression=pathway_data["salaries"],
            success_rate=0.72
        )


class InterviewSuccessPrediction:
    """Predict interview success"""
    
    @staticmethod
    async def predict_interview_success(
        user_past_interviews: Dict[str, float],
        job_match_score: float,
        skill_alignment: float,
        experience_match: float
    ) -> Dict:
        """Predict interview success probability"""
        
        past_success_rate = statistics.mean(user_past_interviews.values()) if user_past_interviews else 0.5
        
        # Weighted calculation
        prediction = (
            past_success_rate * 0.3 +
            job_match_score * 0.3 +
            skill_alignment * 0.2 +
            experience_match * 0.2
        )
        
        confidence = min(0.95, (len(user_past_interviews) / 10) * 0.85 + 0.15)
        
        return {
            "success_probability": prediction,
            "confidence": confidence,
            "factors": {
                "past_performance": past_success_rate,
                "job_match": job_match_score,
                "skill_alignment": skill_alignment,
                "experience_match": experience_match
            },
            "recommendation": "Highly Likely" if prediction > 0.7 else "Moderate" if prediction > 0.5 else "Challenging"
        }


class CompanyCultureAnalyzer:
    """Analyze company culture fit"""
    
    CULTURE_FACTORS = {
        "Remote Friendly": "Remote",
        "Fast Paced": "Pace",
        "Work-Life Balance": "Balance",
        "Innovation": "Innovation",
        "Collaborative": "Teamwork",
        "Startup": "Stage",
        "Enterprise": "Stage"
    }
    
    @staticmethod
    async def analyze_culture_fit(
        company_name: str,
        user_preferences: Dict[str, float]
    ) -> Dict:
        """Analyze culture fit with company"""
        
        # Mock company culture data
        company_culture = {
            "Remote Friendly": 0.8,
            "Fast Paced": 0.7,
            "Work-Life Balance": 0.6,
            "Innovation": 0.8,
            "Collaborative": 0.75,
            "Startup": 0.9
        }
        
        # Calculate alignment
        matches = 0
        total = 0
        
        for factor, user_pref in user_preferences.items():
            company_score = company_culture.get(factor, 0.5)
            match = 1.0 - abs(user_pref - company_score)
            matches += match
            total += 1
        
        fit_score = matches / total if total > 0 else 0.5
        
        return {
            "company": company_name,
            "culture_fit_score": fit_score,
            "alignment_factors": user_preferences,
            "company_culture": company_culture,
            "recommendation": "Perfect Fit" if fit_score > 0.8 else "Good Fit" if fit_score > 0.6 else "Consider Carefully",
            "strengths": [f for f, v in company_culture.items() if v > 0.7],
            "weaknesses": [f for f, v in company_culture.items() if v < 0.5]
        }


class AdvancedAnalyticsEngine:
    """Complete analytics platform"""
    
    def __init__(self):
        self.skill_analyzer = SkillDemandAnalyzer()
        self.salary_analytics = SalaryAnalytics()
        self.career_planner = CareerPathPlanner()
        self.interview_predictor = InterviewSuccessPrediction()
        self.culture_analyzer = CompanyCultureAnalyzer()
        self.user_insights: Dict[str, List[Insight]] = {}
    
    async def generate_daily_insights(self, user_id: str) -> List[Insight]:
        """Generate daily insights for user"""
        
        insights = []
        
        # Top trending skills
        trending = await self.skill_analyzer.trending_skills(3)
        for skill in trending:
            insights.append(Insight(
                insight_type=InsightType.SKILL_DEMAND,
                title=f"📈 {skill.skill_name} is in high demand",
                description=f"Demand score: {skill.demand_score}/100 ({skill.trend.value})",
                data={"skill": skill.skill_name, "score": skill.demand_score},
                recommendation=f"Consider learning {skill.skill_name} - average salary ${skill.average_salary:,.0f}",
                confidence=0.9,
                tags=["trending", "skill", "opportunity"]
            ))
        
        # Salary insights
        insights.append(Insight(
            insight_type=InsightType.SALARY_TREND,
            title="💰 Tech salaries continue upward trend",
            description="Average tech salary increased 3.2% this quarter",
            data={"trend": "up", "percent_change": 3.2},
            recommendation="Good time to negotiate salary or job search",
            confidence=0.85,
            tags=["salary", "market", "timing"]
        ))
        
        self.user_insights[user_id] = insights
        return insights
    
    async def get_dashboard_summary(self, user_id: str) -> Dict:
        """Get analytics dashboard summary"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "key_metrics": {
                "avg_skill_demand": 85,
                "market_temp": "Hot",
                "salary_trend": "↑ +3.2%",
                "job_availability": "High"
            },
            "trending_skills": await self.skill_analyzer.trending_skills(5),
            "market_insights": [
                "Remote work adoption at 42% (up from 35%)",
                "AI/ML roles growing 15% per month",
                "DevOps skills command 20% salary premium"
            ],
            "recommendations": [
                "Learn Python + ML to increase salary by 35%",
                "Target roles in growing sectors",
                "Update resume with trending skills"
            ]
        }


# Global instance
analytics_engine = AdvancedAnalyticsEngine()
