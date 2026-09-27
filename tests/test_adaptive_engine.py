"""
Comprehensive test suite for Adaptive Interview Engine.

Tests all 7 mandatory adaptive evaluation behaviors:
1. Strong candidate answer -> deeper or higher difficulty question.
2. Partial candidate answer -> identifies missing concept and probes that specific concept.
3. Completely wrong answer -> diagnostic question first without immediate difficulty demotion.
4. Repeated weak answers -> detects confirmed topic gap and steps down or pivots.
5. Basic correct vs. Advanced struggling -> distinguishes fundamentals from advanced mastery in knowledge profile and scoring.
6. Avoiding repeated questions -> historical question tracking prevents duplicates.
7. Moving to a new topic -> topic rotation once sufficient mastery or boundary evidence is reached.
"""

import pytest
from backend.services.adaptive_engine import AdaptiveEngine, AdaptiveAction
from backend.services.ai_service import MockAIService


class TestAdaptiveEngine:

    # 1. STRONG CANDIDATE ANSWER
    def test_strong_answer_leads_to_deeper_or_harder_question(self):
        """
        If the candidate gives a strong answer:
        - Ask a deeper or slightly more difficult related question.
        """
        evaluation = {
            "score": 9.2,
            "correctness": "correct",
            "understanding_level": "strong",
            "relevant_concepts_identified": ["Decorators & Closures", "Function metadata preservation"],
            "missing_or_misunderstood_concepts": [],
            "knowledge_diagnosis": "understands_deeply"
        }

        # Start at basic -> should advance to intermediate
        decision_from_basic = AdaptiveEngine.decide_next_step(
            current_question_index=1,
            total_questions=5,
            current_topic="Python Core",
            all_topics=["Python Core", "Data Structures"],
            current_difficulty="basic",
            current_evaluation=evaluation,
            recent_questions_in_topic=[],
            knowledge_profile={}
        )

        assert decision_from_basic["action"] == AdaptiveAction.DEEPER
        assert decision_from_basic["next_difficulty"] == "intermediate"

        # Start at intermediate -> should advance to advanced
        decision_from_inter = AdaptiveEngine.decide_next_step(
            current_question_index=1,
            total_questions=5,
            current_topic="Python Core",
            all_topics=["Python Core", "Data Structures"],
            current_difficulty="intermediate",
            current_evaluation=evaluation,
            recent_questions_in_topic=[],
            knowledge_profile={}
        )

        assert decision_from_inter["action"] == AdaptiveAction.DEEPER
        assert decision_from_inter["next_difficulty"] == "advanced"

    # 2. PARTIAL CANDIDATE ANSWER
    def test_partial_answer_probes_specific_missing_concept(self):
        """
        If the candidate gives a partially correct answer:
        - Identify the missing concept.
        - Ask a related question that checks that specific concept.
        - Keep the difficulty steady rather than dropping or escalating.
        """
        missing_concept = "Hash collision handling via open addressing"
        evaluation = {
            "score": 6.0,
            "correctness": "partially_correct",
            "understanding_level": "partial",
            "relevant_concepts_identified": ["Hash Table lookup O(1) average"],
            "missing_or_misunderstood_concepts": [missing_concept],
            "knowledge_diagnosis": "partially_correct_missing_key_element"
        }

        decision = AdaptiveEngine.decide_next_step(
            current_question_index=2,
            total_questions=5,
            current_topic="Data Structures",
            all_topics=["Data Structures", "System Design"],
            current_difficulty="intermediate",
            current_evaluation=evaluation,
            recent_questions_in_topic=[{"topic": "Data Structures", "score": 6.0}],
            knowledge_profile={}
        )

        assert decision["action"] == AdaptiveAction.PROBE_MISSING
        assert decision["target_concept"] == missing_concept
        assert decision["next_difficulty"] == "intermediate"
        assert missing_concept in decision["reason"]

    # 3. COMPLETELY WRONG ANSWER (FIRST STUMBLE)
    def test_completely_wrong_answer_triggers_diagnostic_first(self):
        """
        If the candidate gives an incorrect answer:
        - Do NOT immediately reduce the difficulty.
        - First ask a diagnostic question to determine how much of the underlying concept the candidate actually understands.
        """
        evaluation = {
            "score": 2.0,
            "correctness": "incorrect",
            "understanding_level": "weak",
            "relevant_concepts_identified": [],
            "missing_or_misunderstood_concepts": ["B-Tree disk page locality vs LSM write amplification"],
            "knowledge_diagnosis": "does_not_understand_concept"
        }

        # First stumble in this topic
        decision = AdaptiveEngine.decide_next_step(
            current_question_index=2,
            total_questions=5,
            current_topic="Databases",
            all_topics=["Databases", "System Design"],
            current_difficulty="intermediate",
            current_evaluation=evaluation,
            recent_questions_in_topic=[],  # No previous stumbles
            knowledge_profile={}
        )

        # Must be diagnostic and difficulty must NOT be dropped immediately
        assert decision["action"] == AdaptiveAction.DIAGNOSTIC
        assert decision["next_difficulty"] == "intermediate"
        assert "diagnostic" in decision["reason"].lower()

    # 4. REPEATED WEAK ANSWERS (EVIDENCE GATHERED)
    def test_repeated_weak_answers_steps_down_or_pivots(self):
        """
        After gathering enough evidence (e.g. diagnostic question also failed):
        - Adjust difficulty appropriately or pivot to another topic to give candidate a fair chance.
        """
        evaluation = {
            "score": 1.5,
            "correctness": "incorrect",
            "understanding_level": "weak",
            "relevant_concepts_identified": [],
            "missing_or_misunderstood_concepts": ["Foundational disk layout"],
            "knowledge_diagnosis": "does_not_understand_concept"
        }

        # Candidate previously stumbled on this topic
        past_interactions = [
            {"topic": "Databases", "score": 2.0, "difficulty": "intermediate"}
        ]

        decision = AdaptiveEngine.decide_next_step(
            current_question_index=3,
            total_questions=6,
            current_topic="Databases",
            all_topics=["Databases", "Python Core"],
            current_difficulty="intermediate",
            current_evaluation=evaluation,
            recent_questions_in_topic=past_interactions,
            knowledge_profile={}
        )

        # Now difficulty is stepped down to basic
        assert decision["action"] == AdaptiveAction.EASIER
        assert decision["next_difficulty"] == "basic"

    # 5. BASIC CORRECT BUT STRUGGLING WITH ADVANCED
    def test_basic_correct_vs_advanced_struggling_weighted_scoring(self):
        """
        The system must distinguish between:
        - 'Candidate knows the basics but not the advanced concept'
        - Candidate answering basic questions correctly should NOT be awarded a top overall score.
        """
        # Candidate answers 3 basic questions with 9/10, but fails 2 advanced questions with 2/10
        answers = [
            {"topic": "Python Core", "difficulty": "basic", "score": 9.0, "relevant_concepts_identified": ["Variables", "Loops"]},
            {"topic": "Python Core", "difficulty": "basic", "score": 9.5, "relevant_concepts_identified": ["Lists", "Dicts"]},
            {"topic": "Python Core", "difficulty": "basic", "score": 9.0, "relevant_concepts_identified": ["Functions"]},
            {"topic": "Python Core", "difficulty": "advanced", "score": 2.0, "relevant_concepts_identified": []},
            {"topic": "Python Core", "difficulty": "advanced", "score": 3.0, "relevant_concepts_identified": []},
        ]

        raw_avg, weighted_score, diff_data, topic_data = AdaptiveEngine.calculate_weighted_scoring(answers)

        # Raw average would be (9 + 9.5 + 9 + 2 + 3) / 5 = 6.5
        # Weighted score penalizes failing the heavy advanced questions:
        # Basic weight = 1.0 each (total 3.0), Advanced weight = 2.2 each (total 4.4)
        # Advanced carries 60% of weight!
        assert diff_data["basic"]["avg"] >= 9.0
        assert diff_data["advanced"]["avg"] <= 2.5
        assert weighted_score < raw_avg  # Weighted score must be lower than raw average because of advanced failure!

        # Check knowledge profile updates reflect basic strong, advanced weak
        profile: dict = {}
        for ans in answers:
            profile = AdaptiveEngine.update_knowledge_profile(
                profile,
                topic=ans["topic"],
                difficulty=ans["difficulty"],
                evaluation={
                    "score": ans["score"],
                    "relevant_concepts_identified": ans["relevant_concepts_identified"],
                    "missing_or_misunderstood_concepts": [] if ans["score"] > 5 else ["Advanced concurrency"]
                }
            )

        assert profile["Python Core"]["basic"]["level"] == "Strong"
        assert profile["Python Core"]["advanced"]["level"] == "Weak"

    # 6. AVOIDING REPEATED QUESTIONS
    def test_avoiding_repeated_questions(self):
        """
        Ensure question generator skips questions already present in candidate history.
        """
        previous_questions = [
            "Explain the difference between mutable and immutable types in Python, and how they behave when passed into functions."
        ]

        generated = MockAIService.generate_question(
            job_role="Software Engineer",
            experience_level="Junior",
            topic="Python Core",
            target_difficulty="basic",
            adaptive_action=AdaptiveAction.DEEPER,
            target_concept="Memory Management",
            adaptive_reason="Probe next concept",
            previous_questions=previous_questions
        )

        # Must not return the first question because it was already asked
        assert generated["question_text"] not in previous_questions
        assert "mutable and immutable types" not in generated["question_text"]

    # 7. MOVING TO A NEW TOPIC WHEN NECESSARY
    def test_moving_to_new_topic_after_sufficient_evidence(self):
        """
        When candidate has answered 2+ questions in current topic and demonstrated clear mastery,
        rotate to the next topic in the interview topics list.
        """
        past_interactions = [
            {"topic": "Python Core", "score": 9.0, "difficulty": "intermediate"},
            {"topic": "Python Core", "score": 9.5, "difficulty": "advanced"}
        ]

        current_eval = {
            "score": 9.5,
            "correctness": "correct",
            "understanding_level": "strong",
            "relevant_concepts_identified": ["Advanced Metaprogramming"],
            "missing_or_misunderstood_concepts": [],
            "knowledge_diagnosis": "understands_deeply"
        }

        decision = AdaptiveEngine.decide_next_step(
            current_question_index=2,
            total_questions=5,
            current_topic="Python Core",
            all_topics=["Python Core", "System Design"],
            current_difficulty="advanced",
            current_evaluation=current_eval,
            recent_questions_in_topic=past_interactions,
            knowledge_profile={}
        )

        assert decision["action"] == AdaptiveAction.PIVOT_TOPIC
        assert decision["next_topic"] == "System Design"
        assert "System Design" in decision["reason"]
