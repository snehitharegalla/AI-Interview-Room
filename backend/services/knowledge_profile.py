"""
Knowledge Profile Management Service.

Maintains multi-dimensional, candidate-specific knowledge states across topics
and difficulty levels throughout the adaptive interview.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import KnowledgeProfile, InterviewAnswer


class KnowledgeProfileService:
    """
    Manages real-time knowledge profile updates and persistence.
    """

    @staticmethod
    def update_profile_slot(
        db: Session,
        interview_id: str,
        candidate_id: int,
        topic: str,
        difficulty: str,
        score: float,
        demonstrated_concepts: List[str],
        missing_concepts: List[str]
    ) -> KnowledgeProfile:
        """
        Updates an existing topic-difficulty slot or creates a new one in the database.
        """
        profile = db.query(KnowledgeProfile).filter(
            KnowledgeProfile.interview_id == interview_id,
            KnowledgeProfile.topic == topic,
            KnowledgeProfile.difficulty == difficulty
        ).first()

        if not profile:
            profile = KnowledgeProfile(
                interview_id=interview_id,
                candidate_id=candidate_id,
                topic=topic,
                difficulty=difficulty,
                mastery_score=0.0,
                level="Not demonstrated",
                demonstrated_concepts=[],
                missing_concepts=[],
                attempt_count=0
            )
            db.add(profile)

        profile.attempt_count += 1

        # Smooth mastery score calculation: 0 - 100
        if profile.attempt_count == 1:
            profile.mastery_score = round(score * 10.0, 1)
        else:
            profile.mastery_score = round((profile.mastery_score * 0.4) + (score * 10.0 * 0.6), 1)

        # Merge demonstrated concepts
        current_dem = list(profile.demonstrated_concepts or [])
        for c in demonstrated_concepts:
            if c and c not in current_dem:
                current_dem.append(c)
        profile.demonstrated_concepts = current_dem

        # Merge missing concepts (excluding those now demonstrated)
        current_miss = list(profile.missing_concepts or [])
        for c in missing_concepts:
            if c and c not in current_miss and c not in current_dem:
                current_miss.append(c)
        profile.missing_concepts = [c for c in current_miss if c not in current_dem]

        # Categorize mastery level
        if profile.mastery_score >= 80.0:
            profile.level = "Strong"
        elif profile.mastery_score >= 60.0:
            profile.level = "Moderate"
        elif profile.mastery_score >= 40.0:
            profile.level = "Partial"
        else:
            profile.level = "Weak"

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_candidate_full_profile(db: Session, candidate_id: int) -> List[Dict[str, Any]]:
        """
        Fetches all aggregated knowledge profile slots across all interviews for a candidate.
        """
        profiles = db.query(KnowledgeProfile).filter(
            KnowledgeProfile.candidate_id == candidate_id
        ).all()

        # Consolidate by topic
        topic_map: Dict[str, Dict[str, Any]] = {}
        for p in profiles:
            if p.topic not in topic_map:
                topic_map[p.topic] = {
                    "topic": p.topic,
                    "levels": {},
                    "demonstrated_concepts": set(),
                    "missing_concepts": set(),
                    "average_mastery": 0.0,
                    "total_attempts": 0
                }
            tm = topic_map[p.topic]
            tm["levels"][p.difficulty] = {
                "mastery_score": p.mastery_score,
                "level": p.level
            }
            tm["total_attempts"] += p.attempt_count
            for c in (p.demonstrated_concepts or []):
                tm["demonstrated_concepts"].add(c)
            for c in (p.missing_concepts or []):
                tm["missing_concepts"].add(c)

        result = []
        for topic, data in topic_map.items():
            scores = [lvl["mastery_score"] for lvl in data["levels"].values()]
            avg = sum(scores) / len(scores) if scores else 0.0
            overall_level = "Strong" if avg >= 75 else "Moderate" if avg >= 55 else "Partial" if avg >= 35 else "Weak"
            result.append({
                "topic": topic,
                "mastery_score": round(avg, 1),
                "level": overall_level,
                "levels_breakdown": data["levels"],
                "demonstrated_concepts": sorted(list(data["demonstrated_concepts"])),
                "missing_concepts": sorted(list(data["missing_concepts"] - data["demonstrated_concepts"])),
                "total_attempts": data["total_attempts"]
            })

        return result


knowledge_profile_service = KnowledgeProfileService()
