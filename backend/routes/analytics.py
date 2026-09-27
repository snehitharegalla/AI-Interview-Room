"""
Recruiter Analytics Routes.

Calculates aggregated recruitment performance analytics:
- Average scores and score distribution
- Interview completion rate
- Topic performance breakdown
- Difficulty distribution across interviews
- Candidate hiring recommendation breakdown
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend.database import get_db
from backend.models import Interview, FinalReport, Candidate, InterviewQuestion, User
from backend.security import get_optional_user

router = APIRouter(tags=["Analytics"])


@router.get("")
def get_recruiter_analytics(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns aggregated analytics metrics for the recruiter dashboard.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )
    total_interviews = db.query(Interview).count()
    completed_interviews = db.query(Interview).filter(Interview.status == "completed").count()
    assigned_interviews = db.query(Interview).filter(Interview.status == "assigned").count()
    in_progress_interviews = db.query(Interview).filter(Interview.status == "in_progress").count()

    completion_rate = round((completed_interviews / total_interviews * 100), 1) if total_interviews > 0 else 0.0

    completed_records = db.query(Interview).filter(Interview.status == "completed").all()
    avg_score = round(
        sum(r.weighted_score for r in completed_records) / len(completed_records), 1
    ) if completed_records else 0.0

    # Difficulty distribution among all asked questions
    questions = db.query(InterviewQuestion).all()
    diff_counts = {"basic": 0, "intermediate": 0, "advanced": 0}
    for q in questions:
        d = (q.difficulty or "intermediate").lower()
        if d in diff_counts:
            diff_counts[d] += 1
        else:
            diff_counts["intermediate"] += 1

    # Topic performance breakdown from final reports
    reports = db.query(FinalReport).all()
    topic_scores: Dict[str, list] = {}
    recommendation_counts = {
        "Strong Hire": 0,
        "Hire": 0,
        "Lean Hire": 0,
        "Re-evaluate": 0,
        "No Hire": 0
    }

    for rep in reports:
        rec = rep.hiring_recommendation
        if rec in recommendation_counts:
            recommendation_counts[rec] += 1
        elif "Lean" in rec:
            recommendation_counts["Lean Hire"] += 1
        else:
            recommendation_counts["Re-evaluate"] += 1

        if rep.topic_breakdown and isinstance(rep.topic_breakdown, dict):
            for t, data in rep.topic_breakdown.items():
                if isinstance(data, dict) and "avg" in data:
                    topic_scores.setdefault(t, []).append(float(data["avg"]))

    topic_performance = []
    for topic, scores in topic_scores.items():
        topic_performance.append({
            "topic": topic,
            "average_score": round(sum(scores) / len(scores), 1),
            "sample_count": len(scores)
        })

    # Score distribution brackets
    score_brackets = {
        "9.0 - 10.0 (Exceptional)": 0,
        "7.0 - 8.9 (Proficient)": 0,
        "5.0 - 6.9 (Competent)": 0,
        "< 5.0 (Developing)": 0
    }
    for r in completed_records:
        sc = r.weighted_score
        if sc >= 9.0:
            score_brackets["9.0 - 10.0 (Exceptional)"] += 1
        elif sc >= 7.0:
            score_brackets["7.0 - 8.9 (Proficient)"] += 1
        elif sc >= 5.0:
            score_brackets["5.0 - 6.9 (Competent)"] += 1
        else:
            score_brackets["< 5.0 (Developing)"] += 1

    return {
        "summary": {
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "in_progress_interviews": in_progress_interviews,
            "assigned_interviews": assigned_interviews,
            "completion_rate": completion_rate,
            "average_score": avg_score
        },
        "difficulty_distribution": diff_counts,
        "topic_performance": topic_performance,
        "recommendation_distribution": recommendation_counts,
        "score_distribution": score_brackets,
        "has_data": completed_interviews > 0
    }
