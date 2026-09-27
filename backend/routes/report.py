"""
Report Routes.

Generates and serves comprehensive, depth-weighted final interview evaluation reports.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from backend.database import get_db
from backend.models import (
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    KnowledgeProfile,
    FinalReport
)
from backend.schemas import FinalReportResponse
from backend.models import User
from backend.security import get_optional_user
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.ai_service import ai_service
from fastapi import status
from typing import Optional

router = APIRouter(tags=["Report"])


@router.get("/{interview_id}/report", response_model=FinalReportResponse)
async def get_or_generate_report(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Retrieves existing final report or compiles an in-depth depth-weighted report.
    Zero-leakage security: Candidate users are strictly forbidden from viewing evaluation reports.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Candidates are not permitted to access evaluation reports or internal scoring."
        )

    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    candidate = interview.candidate

    # Check if report is already generated
    existing_report = db.query(FinalReport).filter(FinalReport.interview_id == interview.id).first()
    if existing_report:
        return FinalReportResponse(
            interview_id=interview.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            job_role=candidate.job_role,
            experience_level=candidate.experience_level,
            overall_score=existing_report.overall_score,
            weighted_score=existing_report.weighted_score,
            hiring_recommendation=existing_report.hiring_recommendation,
            recommendation_reasoning=existing_report.recommendation_reasoning or "",
            overall_summary=existing_report.overall_summary or "",
            depth_analysis=existing_report.depth_analysis or "",
            strengths=existing_report.strengths or [],
            areas_for_improvement=existing_report.areas_for_improvement or [],
            topic_breakdown=existing_report.topic_breakdown or {},
            difficulty_breakdown=existing_report.difficulty_breakdown or {},
            demonstrated_concepts=existing_report.demonstrated_concepts or [],
            missing_concepts=existing_report.missing_concepts or [],
            transcript=existing_report.transcript or [],
            generated_at=existing_report.generated_at
        )

    # Compile interview questions and answers
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id
    ).order_by(InterviewQuestion.question_number).all()

    if not questions or not any(q.answer for q in questions):
        raise HTTPException(status_code=400, detail="Cannot generate report: No answers have been submitted yet.")

    answer_history = []
    transcript = []
    all_demonstrated = []
    all_missing = []

    for q in questions:
        if q.answer:
            ans = q.answer
            item = {
                "question_number": q.question_number,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "target_concept": q.target_concept,
                "question_text": q.question_text,
                "candidate_answer": ans.candidate_answer,
                "score": ans.score,
                "correctness": ans.correctness,
                "understanding_level": ans.understanding_level,
                "relevant_concepts_identified": ans.relevant_concepts_identified or [],
                "missing_or_misunderstood_concepts": ans.missing_or_misunderstood_concepts or [],
                "explanation": ans.explanation,
                "adaptive_decision": ans.adaptive_decision or {}
            }
            answer_history.append(item)
            transcript.append(item)

            for c in ans.relevant_concepts_identified or []:
                if c and c not in all_demonstrated:
                    all_demonstrated.append(c)

            for c in ans.missing_or_misunderstood_concepts or []:
                if c and c not in all_missing:
                    all_missing.append(c)

    # Filter demonstrated concepts out of missing
    final_missing = [c for c in all_missing if c not in all_demonstrated]

    # Calculate depth-weighted score & statistics
    raw_avg, weighted_score, diff_data, topic_data = AdaptiveEngine.calculate_weighted_scoring(answer_history)

    # Format transcript for AI
    transcript_str = ""
    for t in transcript:
        transcript_str += f"\nQ{t['question_number']} [{t['topic']} - {t['difficulty']}]: {t['question_text']}\n"
        transcript_str += f"Answer: {t['candidate_answer']}\n"
        transcript_str += f"Score: {t['score']}/10 | Understanding: {t['understanding_level']} | Correctness: {t['correctness']}\n"
        transcript_str += f"Demonstrated: {', '.join(t['relevant_concepts_identified'])}\n"
        transcript_str += f"Missing: {', '.join(t['missing_or_misunderstood_concepts'])}\n"
        decision = t.get('adaptive_decision', {})
        if decision:
            transcript_str += f"Adaptive Action: {decision.get('action')} (Next: {decision.get('next_difficulty')}) - Rationale: {decision.get('reason')}\n"

    # AI Report Generation
    ai_report_data = await ai_service.generate_final_report(
        candidate_name=candidate.name,
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        topics=interview.topics or [interview.current_topic],
        total_questions=len(answer_history),
        raw_score=raw_avg,
        weighted_score=weighted_score,
        diff_data=diff_data,
        topic_data=topic_data,
        demonstrated_concepts=all_demonstrated,
        missing_concepts=final_missing,
        transcript_str=transcript_str
    )

    report = FinalReport(
        interview_id=interview.id,
        overall_score=raw_avg,
        weighted_score=weighted_score,
        hiring_recommendation=ai_report_data.get("hiring_recommendation", "Re-evaluate"),
        recommendation_reasoning=ai_report_data.get("recommendation_reasoning", ""),
        overall_summary=ai_report_data.get("overall_summary", ""),
        depth_analysis=ai_report_data.get("depth_analysis", ""),
        strengths=ai_report_data.get("strengths", all_demonstrated[:4]),
        areas_for_improvement=ai_report_data.get("areas_for_improvement", final_missing[:3]),
        topic_breakdown=topic_data,
        difficulty_breakdown=diff_data,
        demonstrated_concepts=all_demonstrated,
        missing_concepts=final_missing,
        transcript=transcript,
        generated_at=datetime.utcnow()
    )

    db.add(report)
    interview.overall_score = raw_avg
    interview.weighted_score = weighted_score
    interview.status = "completed"
    if not interview.completed_at:
        interview.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(report)

    return FinalReportResponse(
        interview_id=interview.id,
        candidate_name=candidate.name,
        candidate_email=candidate.email,
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        overall_score=report.overall_score,
        weighted_score=report.weighted_score,
        hiring_recommendation=report.hiring_recommendation,
        recommendation_reasoning=report.recommendation_reasoning or "",
        overall_summary=report.overall_summary or "",
        depth_analysis=report.depth_analysis or "",
        strengths=report.strengths or [],
        areas_for_improvement=report.areas_for_improvement or [],
        topic_breakdown=report.topic_breakdown or {},
        difficulty_breakdown=report.difficulty_breakdown or {},
        demonstrated_concepts=report.demonstrated_concepts or [],
        missing_concepts=report.missing_concepts or [],
        transcript=report.transcript or [],
        generated_at=report.generated_at
    )
