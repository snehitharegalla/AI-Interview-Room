from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==========================================
# AUTH SCHEMAS
# ==========================================

class LoginRequest(BaseModel):
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=4)
    role: Optional[str] = None  # candidate, recruiter (optional filter)
    remember_me: bool = False


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=4)
    role: str = Field(..., pattern="^(candidate|recruiter)$")
    # Candidate specific
    job_role: Optional[str] = None
    experience_level: Optional[str] = "Mid-Level"
    # Recruiter specific
    company: Optional[str] = "TechCorp"
    title: Optional[str] = "Technical Recruiter"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    profile: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==========================================
# CANDIDATE-FACING SANITIZED SCHEMAS
# Zero evaluation leakage: No scores, No difficulty, No internal AI strategy
# ==========================================

class CandidateQuestionView(BaseModel):
    question_id: int
    question_number: int
    total_questions: int
    question_text: str
    topic: str
    duration_minutes: Optional[int] = 30


class CandidateInterviewSummary(BaseModel):
    id: str
    title: str
    job_role: str
    experience_level: str
    total_questions: int
    duration_minutes: int
    current_question_index: int
    status: str  # assigned, in_progress, completed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CandidateAnswerSubmitRequest(BaseModel):
    interview_id: str
    question_id: int
    candidate_answer: str = Field(..., min_length=1)


class CandidateAnswerSubmitResponse(BaseModel):
    interview_id: str
    status: str  # "in_progress" or "completed"
    question_completed: int
    total_questions: int
    next_question: Optional[CandidateQuestionView] = None
    message: str


# ==========================================
# RECRUITER & WIZARD SCHEMAS
# ==========================================

class InterviewCreateWizardRequest(BaseModel):
    # Step 1: Basic Info
    title: str = Field(..., min_length=2, max_length=200)
    job_role: str = Field(..., min_length=2, max_length=100)
    experience_level: str = Field(default="Mid-Level")
    description: Optional[str] = None

    # Step 2: Topics
    topics: List[str] = Field(..., min_length=1)

    # Step 3: Difficulty
    difficulty: str = Field(default="intermediate")  # beginner, intermediate, advanced
    difficulty_range: str = Field(default="all")     # beginner, intermediate, advanced, all

    # Step 4: Settings
    total_questions: int = Field(default=5, ge=3, le=15)
    duration_minutes: int = Field(default=30, ge=10, le=120)
    adaptive_mode: str = Field(default="enabled")
    allow_followups: bool = True
    prevent_repeated: bool = True

    # Step 5: Question Configuration
    question_categories: List[str] = Field(default_factory=lambda: ["Technical", "Conceptual"])
    selected_question_ids: List[int] = Field(default_factory=list)
    custom_questions: List[Dict[str, Any]] = Field(default_factory=list)

    # Step 6: Candidate Assignment
    candidate_id: Optional[int] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None


# ==========================================
# QUESTION BANK SCHEMAS
# ==========================================

class QuestionBankItemCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    question_text: str = Field(..., min_length=10)
    topic: str = Field(..., min_length=2, max_length=100)
    difficulty: str = Field(..., pattern="^(basic|intermediate|advanced)$")
    job_role: str = Field(default="Software Engineer")
    question_type: str = Field(default="Technical")  # Technical, Conceptual, Scenario-based, Problem-solving, Behavioral
    target_concept: Optional[str] = None
    expected_key_points: List[str] = Field(default_factory=list)


class QuestionBankItemUpdate(BaseModel):
    title: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    job_role: Optional[str] = None
    question_type: Optional[str] = None
    target_concept: Optional[str] = None
    expected_key_points: Optional[List[str]] = None


class QuestionBankItemResponse(QuestionBankItemCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# NOTIFICATION SCHEMAS
# ==========================================

class NotificationResponse(BaseModel):
    id: int
    role: str
    title: str
    message: str
    type: str
    link: Optional[str] = None
    read: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# LEGACY & INTERNAL INTERVIEW SCHEMAS
# Maintained for full backwards-compatibility with test suite & recruiter views
# ==========================================

class QuestionResponse(BaseModel):
    question_id: int
    question_number: int
    total_questions: int
    question_text: str
    topic: str
    difficulty: str
    target_concept: Optional[str] = None


class AdaptiveDecisionSchema(BaseModel):
    action: str  # DEEPER, PROBE_MISSING, DIAGNOSTIC, EASIER, PIVOT_TOPIC, CONCLUDE
    next_difficulty: str
    next_topic: str
    target_concept: str
    reason: str


class EvaluationResultSchema(BaseModel):
    score: float
    correctness: str
    understanding_level: str
    relevant_concepts_identified: List[str]
    missing_or_misunderstood_concepts: List[str]
    explanation: str
    knowledge_diagnosis: str
    recommended_strategy: str


class AnswerSubmitRequest(BaseModel):
    interview_id: str
    question_id: int
    candidate_answer: str = Field(..., min_length=1)


class AnswerSubmitResponse(BaseModel):
    interview_id: str
    status: str  # "in_progress" or "completed"
    question_completed: int
    total_questions: int
    evaluation: EvaluationResultSchema
    adaptive_decision: AdaptiveDecisionSchema
    next_question: Optional[QuestionResponse] = None
    message: str


class InterviewStartRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    job_role: str
    experience_level: str
    topics: List[str] = Field(default_factory=lambda: ["Python Core", "Data Structures", "System Design"])
    total_questions: int = Field(default=5, ge=3, le=15)
    starting_difficulty: Optional[str] = None


class InterviewStartResponse(BaseModel):
    interview_id: str
    candidate_name: str
    job_role: str
    experience_level: str
    current_topic: str
    total_questions: int
    first_question: QuestionResponse


class KnowledgeProfileItem(BaseModel):
    topic: str
    difficulty: str
    mastery_score: float
    level: str
    demonstrated_concepts: List[str]
    missing_concepts: List[str]
    attempt_count: int


class InterviewStateResponse(BaseModel):
    interview_id: str
    candidate_name: str
    job_role: str
    experience_level: str
    status: str
    current_question_index: int
    total_questions: int
    current_question: Optional[QuestionResponse] = None
    overall_score: float
    weighted_score: float
    knowledge_profile: List[KnowledgeProfileItem]


class FinalReportResponse(BaseModel):
    interview_id: str
    candidate_name: str
    candidate_email: str
    job_role: str
    experience_level: str
    overall_score: float
    weighted_score: float
    hiring_recommendation: str
    recommendation_reasoning: str
    overall_summary: str
    depth_analysis: str
    strengths: List[str]
    areas_for_improvement: List[str]
    topic_breakdown: Dict[str, Any]
    difficulty_breakdown: Dict[str, Any]
    demonstrated_concepts: List[str]
    missing_concepts: List[str]
    transcript: List[Dict[str, Any]]
    generated_at: datetime
