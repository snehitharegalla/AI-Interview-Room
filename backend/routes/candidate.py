"""
Candidate Experience & Assessment Room Routes.

STRICT SECURITY RULE:
All endpoints here are sanitized. Candidate clients NEVER receive:
- Scores or raw grades
- AI evaluations or feedback
- Difficulty ratings
- Missing concepts or internal diagnoses
- Adaptive engine strategies or decisions
- Recruiter notes or final reports
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.database import get_db
from backend.models import (
    Candidate,
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    Notification,
    KnowledgeProfile,
    FinalReport,
    User
)
from backend.schemas import (
    CandidateInterviewSummary,
    CandidateQuestionView,
    CandidateAnswerSubmitRequest,
    CandidateAnswerSubmitResponse,
    NotificationResponse
)
from backend.security import get_current_user, get_optional_user, require_candidate
from backend.services.adaptive_engine import AdaptiveEngine, AdaptiveAction
from backend.services.evaluator import evaluator_service
from backend.services.question_generator import question_generator
from backend.services.knowledge_profile import knowledge_profile_service
from backend.services.fair_scoring import fair_scoring_service
from backend.services.ai_service import ai_service

router = APIRouter(tags=["Candidate"])


@router.get("/dashboard")
def get_candidate_dashboard(
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db)
):
    """
    Returns candidate dashboard data: assigned, active, and completed assessments.
    Zero score leakage!
    """
    candidate = current_user.candidate_profile
    if not candidate:
        # Auto-create if missing
        candidate = Candidate(
            user_id=current_user.id,
            name=current_user.full_name,
            email=current_user.email,
            job_role="Software Engineer",
            experience_level="Mid-Level"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    interviews = db.query(Interview).filter(
        Interview.candidate_id == candidate.id
    ).order_by(Interview.started_at.desc()).all()

    assigned_list = []
    in_progress_list = []
    completed_list = []

    for item in interviews:
        summary = {
            "id": item.id,
            "title": item.title or f"{item.current_topic} Technical Interview",
            "job_role": candidate.job_role,
            "experience_level": candidate.experience_level,
            "total_questions": item.total_questions,
            "duration_minutes": item.duration_minutes or 30,
            "current_question_index": item.current_question_index,
            "status": item.status,
            "started_at": item.started_at.isoformat() if item.started_at else None,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None
        }
        if item.status == "assigned":
            assigned_list.append(summary)
        elif item.status == "in_progress":
            in_progress_list.append(summary)
        else:
            completed_list.append(summary)

    # Notifications
    notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(10).all()

    notif_data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "read": n.read,
            "created_at": n.created_at.isoformat()
        }
        for n in notifs
    ]

    return {
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "job_role": candidate.job_role,
            "experience_level": candidate.experience_level
        },
        "assigned_interviews": assigned_list,
        "in_progress_interviews": in_progress_list,
        "completed_interviews": completed_list,
        "notifications": notif_data
    }


@router.get("/interview/{interview_id}")
async def get_candidate_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns sanitized interview state for candidate.
    Zero scores, zero evaluations, zero internal telemetry.
    Automatically generates Question 1 if not yet generated so candidate room never hangs.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Find the current pending question
    current_q = None
    if interview.status != "completed":
        if interview.current_question_index == 0:
            interview.current_question_index = 1
        if interview.status == "assigned":
            interview.status = "in_progress"
            if not interview.started_at:
                interview.started_at = datetime.utcnow()
            db.commit()

        q = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id,
            InterviewQuestion.question_number == interview.current_question_index
        ).first()

        # If question does not exist yet, automatically generate Question 1
        if not q:
            candidate = interview.candidate
            topics = interview.topics or ["Python Core", "Data Structures", "System Design"]
            initial_topic = interview.current_topic or topics[0]
            exp_level = candidate.experience_level if candidate else "Mid-Level"
            role = candidate.job_role if candidate else "Software Engineer"
            diff_range = getattr(interview, 'difficulty_range', 'all')
            initial_difficulty = AdaptiveEngine.evaluate_initial_difficulty(exp_level, diff_range)

            try:
                first_q_data = await question_generator.generate_question(
                    job_role=role,
                    experience_level=exp_level,
                    topic=initial_topic,
                    target_difficulty=initial_difficulty,
                    adaptive_action=AdaptiveAction.DEEPER,
                    target_concept=f"Core principles of {initial_topic}",
                    adaptive_reason="Initial benchmark question tailored to candidate profile.",
                    previous_questions=[]
                )
            except Exception as e:
                from backend.services.ai_service import MockAIService
                first_q_data = MockAIService.generate_question(
                    job_role=role,
                    experience_level=exp_level,
                    topic=initial_topic,
                    target_difficulty=initial_difficulty,
                    adaptive_action=AdaptiveAction.DEEPER,
                    target_concept=f"Core principles of {initial_topic}",
                    adaptive_reason="Initial benchmark question.",
                    previous_questions=[]
                )

            q = InterviewQuestion(
                interview_id=interview.id,
                question_number=interview.current_question_index,
                question_text=first_q_data["question_text"],
                topic=first_q_data.get("topic", initial_topic),
                difficulty=first_q_data.get("difficulty", initial_difficulty),
                target_concept=first_q_data.get("target_concept", f"Foundations of {initial_topic}"),
                rationale="Initial baseline question"
            )
            db.add(q)
            interview.status = "in_progress"
            interview.current_topic = initial_topic
            if not interview.started_at:
                interview.started_at = datetime.utcnow()
            db.commit()
            db.refresh(q)

        if q:
            current_q = {
                "question_id": q.id,
                "question_number": q.question_number,
                "total_questions": interview.total_questions,
                "question_text": q.question_text,
                "topic": q.topic,
                "duration_minutes": interview.duration_minutes or 30
            }

    return {
        "interview_id": interview.id,
        "title": interview.title or "Technical Assessment",
        "job_role": interview.candidate.job_role if interview.candidate else "Software Engineer",
        "candidate_name": interview.candidate.name if interview.candidate else "Candidate",
        "status": interview.status,
        "current_question_index": interview.current_question_index,
        "total_questions": interview.total_questions,
        "duration_minutes": interview.duration_minutes or 30,
        "current_question": current_q
    }


@router.post("/interview/{interview_id}/start")
async def candidate_start_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Starts an assigned assessment and serves the first question.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="This interview has already been completed.")

    candidate = interview.candidate
    topics = interview.topics or ["Python Core", "Data Structures", "System Design"]
    initial_topic = interview.current_topic or topics[0]

    # If already has question 1, return it
    q1 = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.question_number == 1
    ).first()

    if not q1:
        initial_difficulty = AdaptiveEngine.evaluate_initial_difficulty(
            candidate.experience_level if candidate else "Mid-Level", None
        )
        try:
            first_q_data = await question_generator.generate_question(
                job_role=candidate.job_role if candidate else "Software Engineer",
                experience_level=candidate.experience_level if candidate else "Mid-Level",
                topic=initial_topic,
                target_difficulty=initial_difficulty,
                adaptive_action=AdaptiveAction.DEEPER,
                target_concept=f"Core principles of {initial_topic}",
                adaptive_reason="Initial benchmark question tailored to candidate profile.",
                previous_questions=[]
            )
        except Exception:
            from backend.services.ai_service import MockAIService
            first_q_data = MockAIService.generate_question(
                job_role=candidate.job_role if candidate else "Software Engineer",
                experience_level=candidate.experience_level if candidate else "Mid-Level",
                topic=initial_topic,
                target_difficulty=initial_difficulty,
                adaptive_action=AdaptiveAction.DEEPER,
                target_concept=f"Core principles of {initial_topic}",
                adaptive_reason="Initial benchmark question.",
                previous_questions=[]
            )

        q1 = InterviewQuestion(
            interview_id=interview.id,
            question_number=1,
            question_text=first_q_data["question_text"],
            topic=first_q_data.get("topic", initial_topic),
            difficulty=first_q_data.get("difficulty", initial_difficulty),
            target_concept=first_q_data.get("target_concept", f"Foundations of {initial_topic}"),
            rationale="Initial baseline question"
        )
        db.add(q1)

        interview.status = "in_progress"
        interview.current_question_index = 1
        interview.current_topic = initial_topic
        if not interview.started_at:
            interview.started_at = datetime.utcnow()
        db.commit()
        db.refresh(q1)

    return {
        "interview_id": interview.id,
        "title": interview.title,
        "job_role": candidate.job_role if candidate else "Software Engineer",
        "status": "in_progress",
        "current_question_index": 1,
        "total_questions": interview.total_questions,
        "current_question": {
            "question_id": q1.id,
            "question_number": 1,
            "total_questions": interview.total_questions,
            "question_text": q1.question_text,
            "topic": q1.topic,
            "duration_minutes": interview.duration_minutes or 30
        }
    }


@router.post("/interview/answer", response_model=CandidateAnswerSubmitResponse)
async def candidate_submit_answer(
    request: CandidateAnswerSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates candidate response internally and decides adaptive next question.
    SANITIZED OUTPUT: Only status and next question text are returned. No scores or reasoning!
    """
    interview = db.query(Interview).filter(Interview.id == request.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="Interview has already been concluded.")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == request.question_id,
        InterviewQuestion.interview_id == interview.id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this interview.")

    if question.answer:
        raise HTTPException(status_code=400, detail="Answer for this question was already submitted.")

    candidate = interview.candidate

    # 1. AI Answer Evaluation (Internal)
    evaluation = await evaluator_service.evaluate_candidate_answer(
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        topic=question.topic,
        difficulty=question.difficulty,
        target_concept=question.target_concept,
        question_text=question.question_text,
        candidate_answer=request.candidate_answer
    )

    # 2. Knowledge Profile Update (Internal)
    knowledge_profile_service.update_profile_slot(
        db=db,
        interview_id=interview.id,
        candidate_id=candidate.id,
        topic=question.topic,
        difficulty=question.difficulty,
        score=evaluation["score"],
        demonstrated_concepts=evaluation.get("relevant_concepts_identified", []),
        missing_concepts=evaluation.get("missing_or_misunderstood_concepts", [])
    )

    # 3. Compile history for adaptive decision
    all_questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id
    ).order_by(InterviewQuestion.question_number).all()

    past_interactions = []
    prev_question_texts = []
    for q in all_questions:
        prev_question_texts.append(q.question_text)
        if q.answer:
            past_interactions.append({
                "question_number": q.question_number,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "score": q.answer.score,
                "understanding_level": q.answer.understanding_level,
                "relevant_concepts_identified": q.answer.relevant_concepts_identified or []
            })

    past_interactions.append({
        "question_number": question.question_number,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "score": evaluation["score"],
        "understanding_level": evaluation["understanding_level"],
        "relevant_concepts_identified": evaluation["relevant_concepts_identified"]
    })

    # Fetch knowledge profile for engine
    db_profiles = db.query(KnowledgeProfile).filter(KnowledgeProfile.interview_id == interview.id).all()
    profile_dict = {}
    for p in db_profiles:
        if p.topic not in profile_dict:
            profile_dict[p.topic] = {}
        profile_dict[p.topic][p.difficulty] = {
            "mastery_score": p.mastery_score,
            "level": p.level,
            "demonstrated_concepts": p.demonstrated_concepts or [],
            "missing_concepts": p.missing_concepts or []
        }

    # 4. Adaptive Engine Decision (Internal)
    adaptive_decision = AdaptiveEngine.decide_next_step(
        current_question_index=interview.current_question_index,
        total_questions=interview.total_questions,
        current_topic=question.topic,
        all_topics=interview.topics or [question.topic],
        current_difficulty=question.difficulty,
        current_evaluation=evaluation,
        recent_questions_in_topic=past_interactions,
        knowledge_profile=profile_dict
    )

    # 5. Persist Answer Record
    answer_record = InterviewAnswer(
        question_id=question.id,
        candidate_answer=request.candidate_answer,
        score=evaluation["score"],
        correctness=evaluation["correctness"],
        understanding_level=evaluation["understanding_level"],
        relevant_concepts_identified=evaluation["relevant_concepts_identified"],
        missing_or_misunderstood_concepts=evaluation["missing_or_misunderstood_concepts"],
        explanation=evaluation["explanation"],
        knowledge_diagnosis=evaluation.get("knowledge_diagnosis"),
        recommended_strategy=evaluation.get("recommended_strategy"),
        adaptive_decision=adaptive_decision,
        timestamp=datetime.utcnow()
    )
    db.add(answer_record)

    # 6. Conclude or Generate Next Question
    if interview.current_question_index >= interview.total_questions or adaptive_decision["action"] == AdaptiveAction.CONCLUDE:
        interview.status = "completed"
        interview.completed_at = datetime.utcnow()

        # Compile complete transcript and concept collections
        transcript = []
        all_demonstrated = []
        all_missing = []

        for q in all_questions:
            ans = q.answer if q.id != question.id else answer_record
            if ans:
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
                transcript.append(item)

                for c in ans.relevant_concepts_identified or []:
                    if c and c not in all_demonstrated:
                        all_demonstrated.append(c)

                for c in ans.missing_or_misunderstood_concepts or []:
                    if c and c not in all_missing:
                        all_missing.append(c)

        final_missing = [c for c in all_missing if c not in all_demonstrated]

        # Compute fair scores and difficulty breakdowns internally
        raw_avg, weighted_score, diff_data, topic_data, rec, rec_reason = fair_scoring_service.calculate(transcript)
        interview.overall_score = raw_avg
        interview.weighted_score = weighted_score

        # Auto-generate and persist FinalReport if not already existing
        existing_report = db.query(FinalReport).filter(FinalReport.interview_id == interview.id).first()
        if not existing_report:
            transcript_str = ""
            for t in transcript:
                transcript_str += f"\nQ{t['question_number']} [{t['topic']} - {t['difficulty']}]: {t['question_text']}\n"
                transcript_str += f"Answer: {t['candidate_answer']}\n"
                transcript_str += f"Score: {t['score']}/10 | Understanding: {t['understanding_level']} | Correctness: {t['correctness']}\n"
                transcript_str += f"Demonstrated: {', '.join(t['relevant_concepts_identified'])}\n"
                transcript_str += f"Missing: {', '.join(t['missing_or_misunderstood_concepts'])}\n"

            ai_report_data = await ai_service.generate_final_report(
                candidate_name=candidate.name,
                job_role=candidate.job_role,
                experience_level=candidate.experience_level,
                topics=interview.topics or [interview.current_topic],
                total_questions=len(transcript),
                raw_score=raw_avg,
                weighted_score=weighted_score,
                diff_data=diff_data,
                topic_data=topic_data,
                demonstrated_concepts=all_demonstrated,
                missing_concepts=final_missing,
                transcript_str=transcript_str
            )

            final_report = FinalReport(
                interview_id=interview.id,
                overall_score=raw_avg,
                weighted_score=weighted_score,
                hiring_recommendation=ai_report_data.get("hiring_recommendation", rec),
                recommendation_reasoning=ai_report_data.get("recommendation_reasoning", rec_reason),
                overall_summary=ai_report_data.get("overall_summary", f"Technical evaluation for {candidate.name} ({candidate.job_role})."),
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
            db.add(final_report)

        # Create notification for recruiter
        if interview.recruiter_id:
            recruiter = interview.recruiter
            if recruiter and recruiter.user_id:
                rec_notif = Notification(
                    user_id=recruiter.user_id,
                    role="recruiter",
                    title="Interview Completed",
                    message=f"Candidate {candidate.name} has completed the {interview.title}. Final report generated.",
                    type="interview_completed",
                    link=f"/report.html?id={interview.id}"
                )
                db.add(rec_notif)

        # Create notification for candidate
        if candidate.user_id:
            cand_notif = Notification(
                user_id=candidate.user_id,
                role="candidate",
                title="Assessment Submitted",
                message=f"You have successfully submitted your responses for '{interview.title}'.",
                type="interview_submitted"
            )
            db.add(cand_notif)

        db.commit()

        return CandidateAnswerSubmitResponse(
            interview_id=interview.id,
            status="completed",
            question_completed=interview.current_question_index,
            total_questions=interview.total_questions,
            next_question=None,
            message="Interview completed successfully. Your responses have been submitted for evaluation."
        )

    # Step 7: Advance to next adaptive question
    next_index = interview.current_question_index + 1
    interview.current_question_index = next_index
    interview.current_topic = adaptive_decision["next_topic"]

    try:
        next_q_data = await question_generator.generate_question(
            job_role=candidate.job_role,
            experience_level=candidate.experience_level,
            topic=adaptive_decision["next_topic"],
            target_difficulty=adaptive_decision["next_difficulty"],
            adaptive_action=adaptive_decision["action"],
            target_concept=adaptive_decision["target_concept"],
            adaptive_reason=adaptive_decision["reason"],
            previous_questions=prev_question_texts
        )
    except Exception as e:
        from backend.services.ai_service import MockAIService
        next_q_data = MockAIService.generate_question(
            job_role=candidate.job_role,
            experience_level=candidate.experience_level,
            topic=adaptive_decision["next_topic"],
            target_difficulty=adaptive_decision["next_difficulty"],
            adaptive_action=adaptive_decision["action"],
            target_concept=adaptive_decision["target_concept"],
            adaptive_reason=adaptive_decision["reason"],
            previous_questions=prev_question_texts
        )

    next_question = InterviewQuestion(
        interview_id=interview.id,
        question_number=next_index,
        question_text=next_q_data["question_text"],
        topic=next_q_data.get("topic", adaptive_decision["next_topic"]),
        difficulty=next_q_data.get("difficulty", adaptive_decision["next_difficulty"]),
        target_concept=next_q_data.get("target_concept", adaptive_decision["target_concept"]),
        rationale=next_q_data.get("rationale", adaptive_decision["reason"])
    )
    db.add(next_question)
    db.commit()
    db.refresh(next_question)

    return CandidateAnswerSubmitResponse(
        interview_id=interview.id,
        status="in_progress",
        question_completed=next_index - 1,
        total_questions=interview.total_questions,
        next_question=CandidateQuestionView(
            question_id=next_question.id,
            question_number=next_index,
            total_questions=interview.total_questions,
            question_text=next_question.question_text,
            topic=next_question.topic,
            duration_minutes=interview.duration_minutes or 30
        ),
        message="Response analyzed. Next question ready."
    )
