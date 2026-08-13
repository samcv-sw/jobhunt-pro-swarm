from typing import List, Dict, Any, Optional

class ABTestEngine:
    """
    Engine for managing Subject Line and Message Sequence A/B testing variations.
    Rotates variations evenly across contacts and calculates performance metrics.
    """

    @classmethod
    def select_variant(cls, campaign_id: str, contact_index: int, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Selects an A/B test variant deterministically using contact index rotation.
        """
        if not variants:
            return {
                "variant_id": "default",
                "subject": "Inquiry regarding career opportunities",
                "body_suffix": ""
            }

        selected_idx = contact_index % len(variants)
        variant = variants[selected_idx]
        variant["selected_index"] = selected_idx
        return variant

    @classmethod
    def calculate_stats(cls, variant_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates conversion rates and identifies the winning variation.
        """
        best_variant = None
        highest_conversion = -1.0
        results = []

        for v in variant_metrics:
            sent = max(1, v.get("sent", 0))
            opens = v.get("opens", 0)
            replies = v.get("replies", 0)
            open_rate = round((opens / sent) * 100, 1)
            reply_rate = round((replies / sent) * 100, 1)

            res = {
                "variant_id": v.get("variant_id", "v1"),
                "subject": v.get("subject", ""),
                "sent": sent,
                "opens": opens,
                "replies": replies,
                "open_rate": open_rate,
                "reply_rate": reply_rate
            }
            results.append(res)

            if reply_rate > highest_conversion:
                highest_conversion = reply_rate
                best_variant = v.get("variant_id")

        return {
            "winning_variant": best_variant,
            "highest_reply_rate": highest_conversion,
            "variants_performance": results
        }
