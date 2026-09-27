"""
Fair Depth-Weighted Scoring Service.

Implements rigorous, depth-weighted scoring to prevent candidates from artificially
inflating their overall evaluation by answering only elementary questions correctly.
"""

from typing import List, Dict, Any, Tuple

DIFFICULTY_WEIGHTS = {
    "basic": 1.0,
    "intermediate": 1.5,
    "advanced": 2.2
}


class FairScoringService:
    """
    Computes fair assessment scores, difficulty breakdowns, and hiring recommendations.
    """

    @staticmethod
    def calculate(answers: List[Dict[str, Any]]) -> Tuple[float, float, Dict[str, Any], Dict[str, Any], str, str]:
        """
        Calculates:
        - raw_average (0 - 10)
        - depth_weighted_score (0 - 10)
        - difficulty_breakdown
        - topic_breakdown
        - hiring_recommendation
        - recommendation_reasoning
        """
        if not answers:
            return 0.0, 0.0, {}, {}, "No Hire", "No answers submitted for evaluation."

        raw_scores = []
        weighted_numerator = 0.0
        weighted_denominator = 0.0

        diff_data = {
            "basic": {"count": 0, "total_score": 0.0, "avg": 0.0},
            "intermediate": {"count": 0, "total_score": 0.0, "avg": 0.0},
            "advanced": {"count": 0, "total_score": 0.0, "avg": 0.0}
        }

        topic_data: Dict[str, Dict[str, Any]] = {}

        for ans in answers:
            score = float(ans.get("score", 0.0))
            diff = str(ans.get("difficulty", "intermediate")).lower()
            topic = str(ans.get("topic", "General"))

            raw_scores.append(score)
            weight = DIFFICULTY_WEIGHTS.get(diff, 1.0)

            weighted_numerator += score * weight
            weighted_denominator += 10.0 * weight

            if diff in diff_data:
                diff_data[diff]["count"] += 1
                diff_data[diff]["total_score"] += score

            if topic not in topic_data:
                topic_data[topic] = {"count": 0, "total_score": 0.0, "avg": 0.0, "concepts": []}
            topic_data[topic]["count"] += 1
            topic_data[topic]["total_score"] += score
            for c in ans.get("relevant_concepts_identified", []):
                if c not in topic_data[topic]["concepts"]:
                    topic_data[topic]["concepts"].append(c)

        raw_avg = round(sum(raw_scores) / len(raw_scores), 1)
        weighted_score = round(
            (weighted_numerator / weighted_denominator) * 10.0 if weighted_denominator > 0 else 0.0, 1
        )

        for d, data in diff_data.items():
            if data["count"] > 0:
                data["avg"] = round(data["total_score"] / data["count"], 1)

        for t, data in topic_data.items():
            if data["count"] > 0:
                data["avg"] = round(data["total_score"] / data["count"], 1)

        # Objective hiring recommendation logic based on depth-weighted performance
        adv_avg = diff_data["advanced"]["avg"]
        adv_count = diff_data["advanced"]["count"]
        inter_avg = diff_data["intermediate"]["avg"]
        basic_avg = diff_data["basic"]["avg"]

        if weighted_score >= 8.5 and (adv_count == 0 or adv_avg >= 7.5):
            recommendation = "Strong Hire"
            reasoning = "Candidate demonstrated exceptional conceptual clarity and advanced architectural depth across all evaluated focus areas."
        elif weighted_score >= 7.0 and (adv_count == 0 or adv_avg >= 6.0):
            recommendation = "Hire"
            reasoning = "Consistent solid performance with strong grasp of intermediate engineering concepts and sound problem-solving abilities."
        elif weighted_score >= 5.5:
            if basic_avg >= 8.0 and adv_avg < 5.0 and adv_count > 0:
                recommendation = "Lean Hire (Junior / Associate)"
                reasoning = "Strong command of fundamental basics, but struggles with advanced concurrency, scalability, or internal mechanics."
            else:
                recommendation = "Lean Hire"
                reasoning = "Candidate exhibits decent domain comprehension with occasional gaps in specific nuanced or edge-case scenarios."
        elif weighted_score >= 4.0:
            recommendation = "Re-evaluate"
            reasoning = "Inconsistent responses. Diagnostic probes revealed fundamental conceptual gaps requiring further technical verification."
        else:
            recommendation = "No Hire"
            reasoning = "Significant deficiencies across basic and intermediate topics with multiple diagnostic questions failing to establish competence."

        return raw_avg, weighted_score, diff_data, topic_data, recommendation, reasoning


fair_scoring_service = FairScoringService()
