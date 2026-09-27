"""
Answer Evaluator Service.

Coordinates candidate answer evaluation, schema validation, and score normalization.
"""

import logging
from typing import Dict, Any, Optional
from backend.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class EvaluatorService:
    @staticmethod
    async def evaluate_candidate_answer(
        job_role: str,
        experience_level: str,
        topic: str,
        difficulty: str,
        target_concept: Optional[str],
        question_text: str,
        candidate_answer: str
    ) -> Dict[str, Any]:
        """
        Submits candidate answer to AI evaluator and normalizes output.
        """
        clean_answer = (candidate_answer or "").strip()
        if not clean_answer:
            return {
                "score": 0.0,
                "correctness": "incorrect",
                "understanding_level": "weak",
                "relevant_concepts_identified": [],
                "missing_or_misunderstood_concepts": [target_concept or f"Core concept of {topic}"],
                "explanation": "No substantive answer was provided.",
                "knowledge_diagnosis": "does_not_understand_concept",
                "recommended_strategy": "Ask a basic diagnostic question."
            }

        result = await ai_service.evaluate_answer(
            job_role=job_role,
            experience_level=experience_level,
            topic=topic,
            difficulty=difficulty,
            target_concept=target_concept or topic,
            question_text=question_text,
            candidate_answer=clean_answer
        )

        # Normalize score
        raw_score = result.get("score", 5.0)
        try:
            score = max(0.0, min(10.0, float(raw_score)))
        except (ValueError, TypeError):
            score = 5.0
        result["score"] = round(score, 1)

        # Normalize understanding level
        level = str(result.get("understanding_level", "moderate")).lower()
        if level not in ["strong", "moderate", "partial", "weak"]:
            if score >= 8.0:
                level = "strong"
            elif score >= 6.0:
                level = "moderate"
            elif score >= 4.0:
                level = "partial"
            else:
                level = "weak"
        result["understanding_level"] = level

        # Normalize correctness
        correctness = str(result.get("correctness", "partially_correct")).lower()
        if correctness not in ["correct", "partially_correct", "incorrect"]:
            if score >= 7.5:
                correctness = "correct"
            elif score >= 4.0:
                correctness = "partially_correct"
            else:
                correctness = "incorrect"
        result["correctness"] = correctness

        # Ensure concept lists
        if not isinstance(result.get("relevant_concepts_identified"), list):
            result["relevant_concepts_identified"] = []
        if not isinstance(result.get("missing_or_misunderstood_concepts"), list):
            result["missing_or_misunderstood_concepts"] = []

        return result


evaluator_service = EvaluatorService()
