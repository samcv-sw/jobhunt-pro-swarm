"""
Automated A/B Testing & Multi-Armed Bandit Subject Line Optimizer for JobHunt Pro.
"""

from typing import List, Dict, Any
import random


def generate_subject_line_variants(topic: str, target_role: str) -> List[Dict[str, Any]]:
    """
    Generates 3 optimized A/B subject line variants.
    """
    return [
        {
            "variant_id": "var_a",
            "subject": f"Quick question regarding {topic} strategy",
            "style": "Direct & Professional",
            "impressions": 0,
            "opens": 0,
            "replies": 0
        },
        {
            "variant_id": "var_b",
            "subject": f"Ideas for {target_role} team growth",
            "style": "Consultative & Value-First",
            "impressions": 0,
            "opens": 0,
            "replies": 0
        },
        {
            "variant_id": "var_c",
            "subject": f"Thought you might find this useful for {topic}",
            "style": "Curiosity & Insight",
            "impressions": 0,
            "opens": 0,
            "replies": 0
        }
    ]


def select_winning_variant(variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Multi-armed bandit variant selection based on reply rate and open rate.
    """
    if not variants:
        return {}

    best_variant = variants[0]
    best_rate = -1.0

    for var in variants:
        impressions = var.get("impressions", 1) or 1
        opens = var.get("opens", 0)
        replies = var.get("replies", 0)
        
        # Weighted conversion score (replies weighted 3x over opens)
        conversion_score = (replies * 3.0 + opens * 1.0) / float(impressions)
        
        if conversion_score > best_rate:
            best_rate = conversion_score
            best_variant = var

    return best_variant
