"""
Interview Routes.

Handles session initialization, question serving, answer evaluation,
and adaptive progression.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from backend.database import get_db
from backend.models import (
    Candidate,
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    KnowledgeProfile,
    User
)
from backend.security import get_optional_user
from typing import Optional
from backend.schemas import (
    InterviewStartRequest,
    InterviewStartResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    InterviewStateResponse,
    QuestionResponse,
    EvaluationResultSchema,
    AdaptiveDecisionSchema,
    KnowledgeProfileItem
)
from backend.services.adaptive_engine import AdaptiveEngine, AdaptiveAction
from backend.services.evaluator import evaluator_service
from backend.services.ai_service import ai_service

router = APIRouter(tags=["Interview"])


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest, db: Session = Depends(get_db)):
    """
    Initializes candidate, interview session, and generates the first question.
    """
    # 1. Create or retrieve candidate
    candidate = db.query(Candidate).filter(Candidate.email == request.candidate_email).first()
    if not candidate:
        candidate = Candidate(
            name=request.candidate_name.strip(),
            email=request.candidate_email.strip().lower(),
            job_role=request.job_role.strip(),
            experience_level=request.experience_level.strip()
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    # 2. Determine initial topic & difficulty
    topics = request.topics if request.topics else ["Python Core", "Data Structures", "System Design"]
    initial_topic = topics[0]
    initial_difficulty = AdaptiveEngine.evaluate_initial_difficulty(
        request.experience_level, request.starting_difficulty
    )

    # 3. Create interview record
    interview = Interview(
        candidate_id=candidate.id,
        topics=topics,
        current_topic=initial_topic,
        total_questions=request.total_questions,
        current_question_index=1,
        status="in_progress",
        started_at=datetime.utcnow()
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # 4. Generate first question
    first_q_data = await ai_service.generate_next_question(
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        topic=initial_topic,
        target_difficulty=initial_difficulty,
        adaptive_action=AdaptiveAction.DEEPER,
        target_concept=f"Core principles of {initial_topic}",
        adaptive_reason="Initial benchmark question tailored to candidate experience level.",
        previous_questions=[]
    )

    first_question = InterviewQuestion(
        interview_id=interview.id,
        question_number=1,
        question_text=first_q_data["question_text"],
        topic=first_q_data.get("topic", initial_topic),
        difficulty=first_q_data.get("difficulty", initial_difficulty),
        target_concept=first_q_data.get("target_concept", f"Foundations of {initial_topic}"),
        rationale=first_q_data.get("rationale", "Initial question benchmark")
    )
    db.add(first_question)

    # 5. Initialize knowledge profile slots for topics
    for topic in topics:
        for diff in ["basic", "intermediate", "advanced"]:
            profile_slot = KnowledgeProfile(
                interview_id=interview.id,
                topic=topic,
                difficulty=diff,
                mastery_score=0.0,
                level="Not demonstrated",
                demonstrated_concepts=[],
                missing_concepts=[],
                attempt_count=0
            )
            db.add(profile_slot)

    db.commit()
    db.refresh(first_question)

    return InterviewStartResponse(
        interview_id=interview.id,
        candidate_name=candidate.name,
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        current_topic=initial_topic,
        total_questions=interview.total_questions,
        first_question=QuestionResponse(
            question_id=first_question.id,
            question_number=1,
            total_questions=interview.total_questions,
            question_text=first_question.question_text,
            topic=first_question.topic,
            difficulty=first_question.difficulty,
            target_concept=first_question.target_concept
        )
    )


@router.post("/answer", response_model=AnswerSubmitResponse)
async def submit_answer(request: AnswerSubmitRequest, db: Session = Depends(get_db)):
    """
    Submits candidate answer, evaluates understanding, updates knowledge profile,
    executes adaptive engine decision, and returns the next question or concludes.
    """
    # 1. Fetch interview and question
    interview = db.query(Interview).filter(Interview.id == request.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="Interview has already been completed.")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == request.question_id,
        InterviewQuestion.interview_id == interview.id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this interview.")

    # Check if answer already exists
    if question.answer:
        raise HTTPException(status_code=400, detail="Answer for this question has already been submitted.")

    candidate = interview.candidate

    # 2. Evaluate answer with AI Evaluator
    evaluation = await evaluator_service.evaluate_candidate_answer(
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        topic=question.topic,
        difficulty=question.difficulty,
        target_concept=question.target_concept,
        question_text=question.question_text,
        candidate_answer=request.candidate_answer
    )

    # 3. Update Knowledge Profile in DB
    profile_slot = db.query(KnowledgeProfile).filter(
        KnowledgeProfile.interview_id == interview.id,
        KnowledgeProfile.topic == question.topic,
        KnowledgeProfile.difficulty == question.difficulty
    ).first()

    if not profile_slot:
        profile_slot = KnowledgeProfile(
            interview_id=interview.id,
            topic=question.topic,
            difficulty=question.difficulty,
            mastery_score=0.0,
            level="Not demonstrated",
            demonstrated_concepts=[],
            missing_concepts=[],
            attempt_count=0
        )
        db.add(profile_slot)

    # Calculate updated slot
    score = evaluation["score"]
    profile_slot.attempt_count += 1
    if profile_slot.attempt_count == 1:
        profile_slot.mastery_score = round(score * 10.0, 1)
    else:
        profile_slot.mastery_score = round((profile_slot.mastery_score * 0.4) + (score * 10.0 * 0.6), 1)

    dem_list = list(profile_slot.demonstrated_concepts or [])
    for c in evaluation.get("relevant_concepts_identified", []):
        if c and c not in dem_list:
            dem_list.append(c)
    profile_slot.demonstrated_concepts = dem_list

    miss_list = list(profile_slot.missing_concepts or [])
    for c in evaluation.get("missing_or_misunderstood_concepts", []):
        if c and c not in miss_list and c not in dem_list:
            miss_list.append(c)
    # Remove from missing if now demonstrated
    profile_slot.missing_concepts = [c for c in miss_list if c not in dem_list]

    if profile_slot.mastery_score >= 80:
        profile_slot.level = "Strong"
    elif profile_slot.mastery_score >= 60:
        profile_slot.level = "Moderate"
    elif profile_slot.mastery_score >= 40:
        profile_slot.level = "Partial"
    else:
        profile_slot.level = "Weak"

    # 4. Gather history for Adaptive Engine
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

    # Include current question in history for accurate decision
    past_interactions.append({
        "question_number": question.question_number,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "score": evaluation["score"],
        "understanding_level": evaluation["understanding_level"],
        "relevant_concepts_identified": evaluation["relevant_concepts_identified"]
    })

    # Build memory profile for engine
    db_profiles = db.query(KnowledgeProfile).filter(KnowledgeProfile.interview_id == interview.id).all()
    profile_dict: Dict[str, Dict[str, Any]] = {}
    for p in db_profiles:
        if p.topic not in profile_dict:
            profile_dict[p.topic] = {}
        profile_dict[p.topic][p.difficulty] = {
            "mastery_score": p.mastery_score,
            "level": p.level,
            "demonstrated_concepts": p.demonstrated_concepts or [],
            "missing_concepts": p.missing_concepts or []
        }

    # 5. Run Adaptive Engine
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

    # 6. Save Answer record
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

    # 7. Check if interview should conclude
    if interview.current_question_index >= interview.total_questions or adaptive_decision["action"] == AdaptiveAction.CONCLUDE:
        interview.status = "completed"
        interview.completed_at = datetime.utcnow()

        # Compute final overall scores
        all_answers_data = past_interactions
        raw_avg, weighted_score, _, _ = AdaptiveEngine.calculate_weighted_scoring(all_answers_data)
        interview.overall_score = raw_avg
        interview.weighted_score = weighted_score

        db.commit()

        return AnswerSubmitResponse(
            interview_id=interview.id,
            status="completed",
            question_completed=interview.current_question_index,
            total_questions=interview.total_questions,
            evaluation=EvaluationResultSchema(**evaluation),
            adaptive_decision=AdaptiveDecisionSchema(**adaptive_decision),
            next_question=None,
            message="Interview successfully completed! Generating comprehensive final report."
        )

    # 8. Generate next question according to adaptive decision
    next_q_num = interview.current_question_index + 1
    interview.current_question_index = next_q_num
    interview.current_topic = adaptive_decision["next_topic"]

    # Candidate profile summary string
    all_demonstrated = []
    for p in db_profiles:
        all_demonstrated.extend(p.demonstrated_concepts or [])
    profile_summary = f"Demonstrated: {', '.join(set(all_demonstrated)) if all_demonstrated else 'None'}"

    try:
        next_q_data = await ai_service.generate_next_question(
            job_role=candidate.job_role,
            experience_level=candidate.experience_level,
            topic=adaptive_decision["next_topic"],
            target_difficulty=adaptive_decision["next_difficulty"],
            adaptive_action=adaptive_decision["action"],
            target_concept=adaptive_decision["target_concept"],
            adaptive_reason=adaptive_decision["reason"],
            previous_questions=prev_question_texts,
            candidate_profile_summary=profile_summary
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
        question_number=next_q_num,
        question_text=next_q_data["question_text"],
        topic=next_q_data.get("topic", adaptive_decision["next_topic"]),
        difficulty=next_q_data.get("difficulty", adaptive_decision["next_difficulty"]),
        target_concept=next_q_data.get("target_concept", adaptive_decision["target_concept"]),
        rationale=next_q_data.get("rationale", adaptive_decision["reason"])
    )
    db.add(next_question)
    db.commit()
    db.refresh(next_question)

    return AnswerSubmitResponse(
        interview_id=interview.id,
        status="in_progress",
        question_completed=question.question_number,
        total_questions=interview.total_questions,
        evaluation=EvaluationResultSchema(**evaluation),
        adaptive_decision=AdaptiveDecisionSchema(**adaptive_decision),
        next_question=QuestionResponse(
            question_id=next_question.id,
            question_number=next_question.question_number,
            total_questions=interview.total_questions,
            question_text=next_question.question_text,
            topic=next_question.topic,
            difficulty=next_question.difficulty,
            target_concept=next_question.target_concept
        ),
        message="Answer evaluated and adaptive question generated."
    )


@router.get("/{interview_id}", response_model=InterviewStateResponse)
async def get_interview_state(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Retrieves current state of an interview session.
    Zero-leakage security: Candidates must use /api/candidate/interview/{id}.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Candidates must use /api/candidate/interview/{id} to maintain zero-leakage security."
        )

    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    candidate = interview.candidate

    if interview.status != "completed":
        if interview.current_question_index == 0:
            interview.current_question_index = 1
        if interview.status == "assigned":
            interview.status = "in_progress"
            if not interview.started_at:
                interview.started_at = datetime.utcnow()
            db.commit()

    # Get active question
    active_q = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.question_number == interview.current_question_index
    ).first()

    # If question does not exist yet and interview is active, auto-generate Question 1
    if not active_q and interview.status != "completed":
        topics = interview.topics or ["Python Core", "Data Structures", "System Design"]
        initial_topic = interview.current_topic or topics[0]
        exp_level = candidate.experience_level if candidate else "Mid-Level"
        role = candidate.job_role if candidate else "Software Engineer"
        diff_range = getattr(interview, 'difficulty_range', 'all')
        initial_difficulty = AdaptiveEngine.evaluate_initial_difficulty(exp_level, diff_range)

        try:
            first_q_data = await ai_service.generate_next_question(
                job_role=role,
                experience_level=exp_level,
                topic=initial_topic,
                target_difficulty=initial_difficulty,
                adaptive_action=AdaptiveAction.DEEPER,
                target_concept=f"Core principles of {initial_topic}",
                adaptive_reason="Initial benchmark question.",
                previous_questions=[]
            )
        except Exception:
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

        active_q = InterviewQuestion(
            interview_id=interview.id,
            question_number=interview.current_question_index,
            question_text=first_q_data["question_text"],
            topic=first_q_data.get("topic", initial_topic),
            difficulty=first_q_data.get("difficulty", initial_difficulty),
            target_concept=first_q_data.get("target_concept", f"Foundations of {initial_topic}"),
            rationale="Initial baseline question"
        )
        db.add(active_q)
        db.commit()
        db.refresh(active_q)

    current_q_resp = None
    if active_q and not active_q.answer:
        current_q_resp = QuestionResponse(
            question_id=active_q.id,
            question_number=active_q.question_number,
            total_questions=interview.total_questions,
            question_text=active_q.question_text,
            topic=active_q.topic,
            difficulty=active_q.difficulty,
            target_concept=active_q.target_concept
        )

    # Get knowledge profile items
    profiles = db.query(KnowledgeProfile).filter(KnowledgeProfile.interview_id == interview.id).all()
    profile_items = [
        KnowledgeProfileItem(
            topic=p.topic,
            difficulty=p.difficulty,
            mastery_score=p.mastery_score,
            level=p.level,
            demonstrated_concepts=p.demonstrated_concepts or [],
            missing_concepts=p.missing_concepts or [],
            attempt_count=p.attempt_count
        )
        for p in profiles
    ]

    return InterviewStateResponse(
        interview_id=interview.id,
        candidate_name=candidate.name,
        job_role=candidate.job_role,
        experience_level=candidate.experience_level,
        status=interview.status,
        current_question_index=interview.current_question_index,
        total_questions=interview.total_questions,
        current_question=current_q_resp,
        overall_score=interview.overall_score,
        weighted_score=interview.weighted_score,
        knowledge_profile=profile_items
    )
