"""
Recruiter Management & 7-Step Interview Wizard Routes.

Provides endpoints for recruiter dashboard metrics, interview creation via multi-step wizard,
candidate management, and full candidate cognitive profile access.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.models import (
    Recruiter,
    Candidate,
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    KnowledgeProfile,
    QuestionBankItem,
    Notification,
    User
)
from backend.schemas import InterviewCreateWizardRequest
from backend.security import get_current_user, require_recruiter, get_optional_user
from backend.services.adaptive_engine import AdaptiveEngine, AdaptiveAction
from backend.services.question_generator import question_generator
from backend.services.knowledge_profile import knowledge_profile_service

router = APIRouter(tags=["Recruiter"])


@router.get("/dashboard")
def get_recruiter_dashboard(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns high-level recruitment metrics, recent interviews, status breakdown,
    and performance distribution. Returns clean empty state indicators if database is fresh.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    total_candidates = db.query(Candidate).count()
    active_interviews = db.query(Interview).filter(Interview.status.in_(["assigned", "in_progress"])).count()
    completed_interviews = db.query(Interview).filter(Interview.status == "completed").count()

    # Average score of completed interviews
    completed_records = db.query(Interview).filter(
        Interview.status == "completed",
        Interview.weighted_score > 0
    ).all()

    avg_score = round(
        sum(r.weighted_score for r in completed_records) / len(completed_records), 1
    ) if completed_records else 0.0

    # Recent interviews list (up to 10)
    recent = db.query(Interview).order_by(Interview.started_at.desc()).limit(10).all()
    recent_data = []
    for item in recent:
        cand = item.candidate
        recent_data.append({
            "id": item.id,
            "title": item.title or f"{item.current_topic} Technical Interview",
            "candidate_name": cand.name if cand else "Unassigned",
            "candidate_email": cand.email if cand else "",
            "job_role": cand.job_role if cand else "Software Engineer",
            "status": item.status,
            "total_questions": item.total_questions,
            "current_question_index": item.current_question_index,
            "weighted_score": item.weighted_score,
            "started_at": item.started_at.strftime("%b %d, %Y") if item.started_at else "-",
            "completed_at": item.completed_at.strftime("%b %d, %Y") if item.completed_at else None,
            "report_url": f"/report.html?id={item.id}" if item.status == "completed" else None
        })

    # Status breakdown
    status_counts = {
        "assigned": db.query(Interview).filter(Interview.status == "assigned").count(),
        "in_progress": db.query(Interview).filter(Interview.status == "in_progress").count(),
        "completed": completed_interviews
    }

    return {
        "metrics": {
            "total_candidates": total_candidates,
            "active_interviews": active_interviews,
            "completed_interviews": completed_interviews,
            "average_score": avg_score
        },
        "recent_interviews": recent_data,
        "status_distribution": status_counts,
        "has_data": total_candidates > 0
    }


@router.get("/interviews")
def list_interviews(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns list of all interviews with search and status filtering.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    query = db.query(Interview)

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Interview.status == status_filter.lower())

    records = query.order_by(Interview.started_at.desc()).all()
    results = []

    for item in records:
        cand = item.candidate
        if search:
            s = search.lower()
            cand_match = cand and (s in cand.name.lower() or s in cand.email.lower() or s in cand.job_role.lower())
            title_match = s in (item.title or "").lower() or s in (item.current_topic or "").lower()
            if not (cand_match or title_match):
                continue

        results.append({
            "id": item.id,
            "title": item.title or "Technical Assessment",
            "candidate_id": cand.id if cand else None,
            "candidate_name": cand.name if cand else "Unassigned",
            "candidate_email": cand.email if cand else "",
            "job_role": cand.job_role if cand else "Software Engineer",
            "experience_level": cand.experience_level if cand else "Mid-Level",
            "topics": item.topics or [],
            "status": item.status,
            "total_questions": item.total_questions,
            "current_question_index": item.current_question_index,
            "weighted_score": item.weighted_score,
            "duration_minutes": item.duration_minutes or 30,
            "started_at": item.started_at.strftime("%b %d, %Y") if item.started_at else "-",
            "completed_at": item.completed_at.strftime("%b %d, %Y") if item.completed_at else None,
            "report_url": f"/report.html?id={item.id}" if item.status == "completed" else None
        })

    return results


@router.post("/interviews")
async def create_interview_wizard(
    request: InterviewCreateWizardRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Creates and configures an interview through the 7-Step Recruiter Wizard:
    Step 1: Basic Info (Name, Job Role, Experience, Description)
    Step 2: Topics (Python, Java, SQL, OOP, Data Structures, etc.)
    Step 3: Difficulty (Beginner, Intermediate, Advanced, Range)
    Step 4: Settings (Total questions, duration, adaptive mode, follow-ups, repetition prevention)
    Step 5: Question Configuration (Question bank / custom seed questions)
    Step 6: Candidate Assignment (Existing candidate or new invitee)
    Step 7: Review & Finalize
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    # 1. Resolve or Create Candidate
    candidate = None
    if request.candidate_id:
        candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()

    if not candidate and request.candidate_email:
        email_clean = request.candidate_email.strip().lower()
        candidate = db.query(Candidate).filter(Candidate.email == email_clean).first()
        if not candidate:
            candidate = Candidate(
                name=(request.candidate_name or "New Candidate").strip(),
                email=email_clean,
                job_role=request.job_role,
                applied_role=request.job_role,
                experience_level=request.experience_level,
                skills=request.topics
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

    if not candidate:
        # Create placeholder candidate
        candidate = Candidate(
            name="Assigned Candidate",
            email="candidate@example.com",
            job_role=request.job_role,
            applied_role=request.job_role,
            experience_level=request.experience_level,
            skills=request.topics
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    # 2. Resolve Recruiter
    recruiter_id = None
    if current_user and current_user.recruiter_profile:
        recruiter_id = current_user.recruiter_profile.id
    else:
        first_rec = db.query(Recruiter).first()
        if first_rec:
            recruiter_id = first_rec.id

    topics = request.topics if request.topics else ["Python Core", "Data Structures", "System Design"]
    initial_topic = topics[0]

    # 3. Create Interview Record
    interview = Interview(
        title=request.title.strip(),
        description=request.description,
        recruiter_id=recruiter_id,
        candidate_id=candidate.id,
        topics=topics,
        difficulty_range=request.difficulty_range,
        total_questions=request.total_questions,
        duration_minutes=request.duration_minutes,
        adaptive_mode=request.adaptive_mode,
        allow_followups=1 if request.allow_followups else 0,
        prevent_repeated=1 if request.prevent_repeated else 0,
        current_topic=initial_topic,
        current_question_index=1,
        status="assigned",
        started_at=datetime.utcnow()
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # 4. Prepare Question 1: Check if recruiter selected starter questions from bank
    first_question_text = None
    first_q_difficulty = request.difficulty.lower()
    first_q_concept = f"Core fundamentals of {initial_topic}"

    if request.selected_question_ids:
        q_item = db.query(QuestionBankItem).filter(
            QuestionBankItem.id == request.selected_question_ids[0]
        ).first()
        if q_item:
            first_question_text = q_item.question_text
            initial_topic = q_item.topic
            first_q_difficulty = q_item.difficulty
            first_q_concept = q_item.target_concept or first_q_concept

    if not first_question_text:
        # Generate with QuestionGeneratorService within recruiter's boundaries
        initial_difficulty = AdaptiveEngine.evaluate_initial_difficulty(
            request.experience_level, request.difficulty
        )
        first_q_data = await question_generator.generate_question(
            job_role=request.job_role,
            experience_level=request.experience_level,
            topic=initial_topic,
            target_difficulty=initial_difficulty,
            adaptive_action=AdaptiveAction.DEEPER,
            target_concept=f"Core principles of {initial_topic}",
            adaptive_reason="Initial benchmark question configured by recruiter wizard.",
            previous_questions=[]
        )
        first_question_text = first_q_data["question_text"]
        first_q_difficulty = first_q_data.get("difficulty", initial_difficulty)
        first_q_concept = first_q_data.get("target_concept", f"Foundations of {initial_topic}")

    first_question = InterviewQuestion(
        interview_id=interview.id,
        question_number=1,
        question_text=first_question_text,
        topic=initial_topic,
        difficulty=first_q_difficulty,
        target_concept=first_q_concept,
        question_type="Technical",
        rationale="Question 1 generated within recruiter boundaries."
    )
    db.add(first_question)

    # 5. Initialize Knowledge Profile slots for configured topics
    for t in topics:
        for d in ["basic", "intermediate", "advanced"]:
            slot = KnowledgeProfile(
                interview_id=interview.id,
                candidate_id=candidate.id,
                topic=t,
                difficulty=d,
                mastery_score=0.0,
                level="Not demonstrated",
                demonstrated_concepts=[],
                missing_concepts=[],
                attempt_count=0
            )
            db.add(slot)

    # 6. Send notification to candidate
    if candidate.user_id:
        notif = Notification(
            user_id=candidate.user_id,
            role="candidate",
            title="New Interview Assigned",
            message=f"You have been assigned '{interview.title}' for {interview.candidate.job_role}.",
            type="interview_assigned",
            link=f"/interview.html?id={interview.id}"
        )
        db.add(notif)

    db.commit()

    return {
        "status": "success",
        "interview_id": interview.id,
        "title": interview.title,
        "candidate_name": candidate.name,
        "candidate_email": candidate.email,
        "topics": interview.topics,
        "total_questions": interview.total_questions,
        "message": "Interview successfully created and assigned to candidate!"
    }


@router.get("/candidates")
def list_candidates(
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns candidate directory with search, filters, latest score, and interview status.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    candidates = db.query(Candidate).all()
    results = []

    for c in candidates:
        if search:
            s = search.lower()
            if s not in c.name.lower() and s not in c.email.lower() and s not in c.job_role.lower():
                continue

        if role_filter and role_filter.lower() != "all":
            if role_filter.lower() not in c.job_role.lower():
                continue

        # Get latest interview
        latest_interview = db.query(Interview).filter(
            Interview.candidate_id == c.id
        ).order_by(Interview.started_at.desc()).first()

        status_label = latest_interview.status if latest_interview else "None"
        latest_score = latest_interview.weighted_score if latest_interview and latest_interview.status == "completed" else None
        interview_date = latest_interview.started_at.strftime("%b %d, %Y") if latest_interview else "-"

        results.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "job_role": c.job_role,
            "applied_role": c.applied_role or c.job_role,
            "experience_level": c.experience_level,
            "status": status_label,
            "latest_score": latest_score,
            "interview_date": interview_date,
            "latest_interview_id": latest_interview.id if latest_interview else None,
            "skills": c.skills or []
        })

    return results


@router.get("/candidate/{candidate_id}")
def get_candidate_details(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns complete candidate profile modal data:
    - Basic Information
    - Interview History
    - Skills & Performance
    - Live Cognitive Knowledge Profile (Strengths & Gaps)
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Interview history
    interviews = db.query(Interview).filter(
        Interview.candidate_id == candidate.id
    ).order_by(Interview.started_at.desc()).all()

    interview_history = []
    for item in interviews:
        interview_history.append({
            "id": item.id,
            "title": item.title or "Technical Assessment",
            "status": item.status,
            "total_questions": item.total_questions,
            "weighted_score": item.weighted_score,
            "started_at": item.started_at.strftime("%b %d, %Y") if item.started_at else "-",
            "completed_at": item.completed_at.strftime("%b %d, %Y") if item.completed_at else "-",
            "report_url": f"/report.html?id={item.id}" if item.status == "completed" else None
        })

    # Cognitive Knowledge Profile aggregated across interviews
    knowledge_profile = knowledge_profile_service.get_candidate_full_profile(db, candidate.id)

    # Strengths and areas for improvement
    strengths = []
    areas_for_improvement = []
    for kp in knowledge_profile:
        for dem in kp.get("demonstrated_concepts", []):
            if dem not in strengths:
                strengths.append(dem)
        for miss in kp.get("missing_concepts", []):
            if miss not in areas_for_improvement and miss not in strengths:
                areas_for_improvement.append(miss)

    return {
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "job_role": candidate.job_role,
            "applied_role": candidate.applied_role or candidate.job_role,
            "experience_level": candidate.experience_level,
            "skills": candidate.skills or [],
            "created_at": candidate.created_at.strftime("%b %d, %Y")
        },
        "interview_history": interview_history,
        "knowledge_profile": knowledge_profile,
        "strengths": strengths[:8],
        "areas_for_improvement": areas_for_improvement[:8]
    }
