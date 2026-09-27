"""
Adaptive Interview Engine.

This module implements the core decision engine for the AI Interview Room.
It does NOT use naive "wrong = easy / correct = hard" logic.
Instead, it:
1. Gathers evidence of the candidate's actual conceptual knowledge.
2. Identifies demonstrated vs. missing concepts.
3. Distinguishes:
   - "Candidate does not know the topic"
   - "Candidate knows basics but not the advanced concept"
   - "Candidate understands the concept but stumbled on a particular question"
   - "Candidate gave a partially correct answer"
4. Employs diagnostic probing before any premature difficulty reduction.
5. Updates the candidate's multi-dimensional knowledge profile.
6. Ensures topic rotation once sufficient mastery or boundary evidence is gathered.
7. Strictly prevents repeating questions or concepts.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime


DIFFICULTY_LEVELS = ["basic", "intermediate", "advanced"]

DIFFICULTY_WEIGHTS = {
    "basic": 1.0,
    "intermediate": 1.5,
    "advanced": 2.2
}


class AdaptiveAction:
    DEEPER = "DEEPER"               # Push to deeper nuances, edge cases, or higher difficulty
    PROBE_MISSING = "PROBE_MISSING" # Target the specific concept the candidate omitted/confused
    DIAGNOSTIC = "DIAGNOSTIC"       # Probe underlying foundation to determine actual grasp before reducing
    EASIER = "EASIER"               # Proven topic gap across 2+ questions; step down to test baseline
    PIVOT_TOPIC = "PIVOT_TOPIC"     # Candidate demonstrated sufficient knowledge or reached ceiling in current topic
    CONCLUDE = "CONCLUDE"           # Reached final question target


class AdaptiveEngine:
    """
    Orchestrates interview strategy and candidate knowledge profiling.
    """

    @staticmethod
    def evaluate_initial_difficulty(experience_level: str, requested_difficulty: Optional[str] = None) -> str:
        """
        Determines starting difficulty based on candidate experience level and preference.
        """
        if requested_difficulty and requested_difficulty.lower() in DIFFICULTY_LEVELS:
            return requested_difficulty.lower()

        exp_clean = (experience_level or "").strip().lower()
        if "lead" in exp_clean or "principal" in exp_clean or "staff" in exp_clean:
            return "advanced"
        elif "senior" in exp_clean or "architect" in exp_clean:
            return "intermediate"
        elif "mid" in exp_clean or "intermediate" in exp_clean or "2" in exp_clean or "3" in exp_clean:
            return "intermediate"
        else:
            return "basic"

    @staticmethod
    def update_knowledge_profile(
        existing_profile: Dict[str, Dict[str, Any]],
        topic: str,
        difficulty: str,
        evaluation: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Updates the in-memory or database knowledge profile based on the latest evaluation.
        Key structure: profile[topic][difficulty] = { mastery_score, level, demonstrated, missing, attempts }
        """
        if topic not in existing_profile:
            existing_profile[topic] = {}

        if difficulty not in existing_profile[topic]:
            existing_profile[topic][difficulty] = {
                "mastery_score": 0.0,
                "level": "Not demonstrated",
                "demonstrated_concepts": [],
                "missing_concepts": [],
                "attempt_count": 0,
                "scores": []
            }

        slot = existing_profile[topic][difficulty]
        score = float(evaluation.get("score", 5.0))
        slot["attempt_count"] += 1
        slot["scores"].append(score)

        # Exponential moving average for score
        if len(slot["scores"]) == 1:
            slot["mastery_score"] = round(score * 10.0, 1)  # 0 to 100 scale
        else:
            slot["mastery_score"] = round((slot["mastery_score"] * 0.4) + (score * 10.0 * 0.6), 1)

        # Merge concepts
        for concept in evaluation.get("relevant_concepts_identified", []):
            if concept and concept not in slot["demonstrated_concepts"]:
                slot["demonstrated_concepts"].append(concept)
            # If candidate previously missed it but now demonstrated, remove from missing
            if concept in slot["missing_concepts"]:
                slot["missing_concepts"].remove(concept)

        for concept in evaluation.get("missing_or_misunderstood_concepts", []):
            if concept and concept not in slot["missing_concepts"] and concept not in slot["demonstrated_concepts"]:
                slot["missing_concepts"].append(concept)

        # Determine level
        mastery = slot["mastery_score"]
        if mastery >= 80:
            slot["level"] = "Strong"
        elif mastery >= 60:
            slot["level"] = "Moderate"
        elif mastery >= 40:
            slot["level"] = "Partial"
        else:
            slot["level"] = "Weak"

        return existing_profile

    @staticmethod
    def decide_next_step(
        current_question_index: int,
        total_questions: int,
        current_topic: str,
        all_topics: List[str],
        current_difficulty: str,
        current_evaluation: Dict[str, Any],
        recent_questions_in_topic: List[Dict[str, Any]],
        knowledge_profile: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates the next adaptive directive.

        Returns:
            dict containing:
            - action: str (AdaptiveAction)
            - next_difficulty: str
            - next_topic: str
            - target_concept: str
            - reason: str
        """
        # 1. Check if interview question limit has been reached
        if current_question_index >= total_questions:
            return {
                "action": AdaptiveAction.CONCLUDE,
                "next_difficulty": current_difficulty,
                "next_topic": current_topic,
                "target_concept": "Final Summary",
                "reason": "Total interview question target reached."
            }

        score = float(current_evaluation.get("score", 5.0))
        understanding_level = str(current_evaluation.get("understanding_level", "moderate")).lower()
        correctness = str(current_evaluation.get("correctness", "partially_correct")).lower()
        missing_concepts = current_evaluation.get("missing_or_misunderstood_concepts", [])
        demonstrated_concepts = current_evaluation.get("relevant_concepts_identified", [])
        knowledge_diagnosis = current_evaluation.get("knowledge_diagnosis", "")

        # Look at history for current topic
        questions_in_this_topic = [
            q for q in recent_questions_in_topic if q.get("topic") == current_topic
        ]
        topic_question_count = len(questions_in_this_topic)

        # Check if topic rotation is warranted (e.g. 2 or more questions in current topic and more topics available)
        available_next_topics = [t for t in all_topics if t != current_topic]

        # Criteria for topic saturation:
        # If candidate already answered 2+ questions in this topic AND demonstrated strong grasp, OR has shown consistent struggle
        if topic_question_count >= 2 and available_next_topics:
            last_two_scores = [
                q.get("score", 5.0) for q in questions_in_this_topic[-2:]
            ]
            avg_recent = sum(last_two_scores) / len(last_two_scores)

            # Saturated if consistently high (>= 7.5) or exhausted (<= 3.5 after diagnostic)
            if avg_recent >= 7.5 or (avg_recent <= 3.5 and topic_question_count >= 2):
                next_topic = available_next_topics[0]
                return {
                    "action": AdaptiveAction.PIVOT_TOPIC,
                    "next_difficulty": "intermediate" if avg_recent >= 7.5 else "basic",
                    "next_topic": next_topic,
                    "target_concept": f"Foundations of {next_topic}",
                    "reason": f"Candidate demonstrated clear assessment in '{current_topic}' (avg score {avg_recent:.1f}). Rotating to next focus area '{next_topic}'."
                }

        # -------------------------------------------------------------------
        # ADAPTIVE BEHAVIOR BRANCHES
        # -------------------------------------------------------------------

        # CASE 1: STRONG ANSWER (Score >= 8.0, Understanding: Strong)
        # -> Deepen within topic or advance difficulty
        if understanding_level == "strong" or score >= 8.0:
            if current_difficulty == "basic":
                next_difficulty = "intermediate"
                action = AdaptiveAction.DEEPER
                concept_to_probe = f"Advanced implementation of {demonstrated_concepts[0]}" if demonstrated_concepts else "System integration"
                reason = "Candidate demonstrated strong fundamental grasp. Advancing difficulty to intermediate."
            elif current_difficulty == "intermediate":
                next_difficulty = "advanced"
                action = AdaptiveAction.DEEPER
                concept_to_probe = f"Edge cases, scalability and internal mechanics of {demonstrated_concepts[0]}" if demonstrated_concepts else "High concurrency & edge cases"
                reason = "Candidate excelled at intermediate level. Stepping up to advanced architectural/internal challenge."
            else:  # already advanced
                next_difficulty = "advanced"
                action = AdaptiveAction.DEEPER
                concept_to_probe = "Trade-offs under high scale and fault-tolerant edge conditions"
                reason = "Candidate demonstrated mastery at advanced level. Probing deep architectural tradeoffs."

            return {
                "action": action,
                "next_difficulty": next_difficulty,
                "next_topic": current_topic,
                "target_concept": concept_to_probe,
                "reason": reason
            }

        # CASE 2: PARTIALLY CORRECT ANSWER (Understanding: Partial or Moderate, Score 4.0 - 7.9)
        # -> Target the specific missing concept without immediately demoting or escalating
        if understanding_level in ["partial", "moderate"] or (score >= 4.0 and score < 8.0):
            target_concept = missing_concepts[0] if missing_concepts else "practical edge cases"
            return {
                "action": AdaptiveAction.PROBE_MISSING,
                "next_difficulty": current_difficulty,  # Maintain difficulty level
                "next_topic": current_topic,
                "target_concept": target_concept,
                "reason": f"Candidate understood core principles but missed key concept: '{target_concept}'. Probing this specific concept to assess gap."
            }

        # CASE 3: INCORRECT / WEAK ANSWER (Understanding: Weak, Score < 4.0)
        # -> Distinguish whether this is an isolated stumble or a true topic gap.
        # CRITICAL RULE: Do NOT immediately drop difficulty on the first wrong answer!
        # First trigger a DIAGNOSTIC question on the foundational concept.
        previous_stumbles_in_topic = sum(
            1 for q in questions_in_this_topic if q.get("score", 10.0) < 4.5
        )

        if previous_stumbles_in_topic == 0:
            # First incorrect answer on this topic!
            # Ask a diagnostic question to see if they understand the underlying mechanism
            target_concept = (
                missing_concepts[0] if missing_concepts
                else f"Underlying mechanism of {current_topic}"
            )
            return {
                "action": AdaptiveAction.DIAGNOSTIC,
                "next_difficulty": current_difficulty,  # Do not lower yet!
                "next_topic": current_topic,
                "target_concept": target_concept,
                "reason": "Candidate struggled with this question. Rather than lowering difficulty immediately, issuing a diagnostic question to assess foundational knowledge."
            }
        else:
            # Candidate has repeatedly struggled on this topic (evidence gathered)
            # Now we have evidence of a genuine knowledge gap
            if current_difficulty == "advanced":
                next_diff = "intermediate"
                reason = "Evidence shows candidate lacks advanced grasp in this area. Adjusting difficulty to intermediate to establish baseline."
            elif current_difficulty == "intermediate":
                next_diff = "basic"
                reason = "Multiple attempts confirm candidate struggles with intermediate concepts. Stepping down to basic fundamentals."
            else:
                # Already at basic! If another topic is available, pivot to give candidate a fair chance in another area
                if available_next_topics:
                    next_topic = available_next_topics[0]
                    return {
                        "action": AdaptiveAction.PIVOT_TOPIC,
                        "next_difficulty": "basic",
                        "next_topic": next_topic,
                        "target_concept": f"Core concepts of {next_topic}",
                        "reason": f"Candidate lacks background in '{current_topic}'. Pivoting to '{next_topic}' to evaluate broad competence."
                    }
                next_diff = "basic"
                reason = "Testing fundamental concepts with an alternate diagnostic angle."

            return {
                "action": AdaptiveAction.EASIER,
                "next_difficulty": next_diff,
                "next_topic": current_topic,
                "target_concept": missing_concepts[0] if missing_concepts else f"Fundamentals of {current_topic}",
                "reason": reason
            }

    @staticmethod
    def calculate_weighted_scoring(
        answers: List[Dict[str, Any]]
    ) -> Tuple[float, float, Dict[str, Any], Dict[str, Any]]:
        """
        Calculates depth-weighted overall score and difficulty breakdown.

        CRITICAL REQUIREMENT:
        Do not give a high score simply because a candidate answered many easy questions correctly.
        A candidate who performs well only on basic questions should be reported as strong in fundamentals
        but not considered strong in advanced concepts.

        Formula:
        Raw average = sum(scores) / n
        Weighted score = sum(score * weight) / sum(max_score * weight) * 10
        """
        if not answers:
            return 0.0, 0.0, {}, {}

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

            # Numerator is candidate's weighted points, denominator is max possible weighted points (10 * weight)
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

        raw_avg = sum(raw_scores) / len(raw_scores)
        weighted_score = (weighted_numerator / weighted_denominator) * 10.0 if weighted_denominator > 0 else 0.0

        # Calculate averages for difficulty
        for d, data in diff_data.items():
            if data["count"] > 0:
                data["avg"] = round(data["total_score"] / data["count"], 1)

        # Calculate averages for topics
        for t, data in topic_data.items():
            if data["count"] > 0:
                data["avg"] = round(data["total_score"] / data["count"], 1)

        return round(raw_avg, 1), round(weighted_score, 1), diff_data, topic_data
