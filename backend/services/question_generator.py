"""
Question Generator Service.

Dedicated service responsible for generating contextually relevant technical interview questions.
Works within the recruiter's configured boundaries (topics, difficulty, role) and adheres
to the strategic directives determined by the Adaptive Interview Engine (DEEPER, PROBE_MISSING,
DIAGNOSTIC, EASIER, PIVOT_TOPIC).
"""

import logging
from typing import Dict, Any, List, Optional
from backend.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    """
    Orchestrates the generation of adaptive questions using AI or curated question bank pools.
    """

    @staticmethod
    async def generate_question(
        job_role: str,
        experience_level: str,
        topic: str,
        target_difficulty: str,
        adaptive_action: str,
        target_concept: str,
        adaptive_reason: str,
        previous_questions: List[str],
        question_type: str = "Technical"
    ) -> Dict[str, Any]:
        """
        Generates the next question matching the adaptive strategy.
        Guarantees that previous questions are strictly avoided.
        """
        logger.info(
            "Generating question: Topic=%s, Diff=%s, Action=%s, TargetConcept=%s",
            topic, target_difficulty, adaptive_action, target_concept
        )

        # Leverage the AI service (which automatically uses Gemini, OpenAI, or intelligent fallback)
        question_data = await ai_service.generate_next_question(
            job_role=job_role,
            experience_level=experience_level,
            topic=topic,
            target_difficulty=target_difficulty,
            adaptive_action=adaptive_action,
            target_concept=target_concept,
            adaptive_reason=adaptive_reason,
            previous_questions=previous_questions
        )

        # Ensure question_type is attached
        if "question_type" not in question_data:
            question_data["question_type"] = question_type

        return question_data


question_generator = QuestionGeneratorService()
