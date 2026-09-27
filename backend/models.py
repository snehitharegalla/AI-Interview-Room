import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean
)
from sqlalchemy.orm import relationship
from backend.database import Base


def generate_uuid():
    return str(uuid.uuid4())[:8]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # "candidate" or "recruiter"
    created_at = Column(DateTime, default=datetime.utcnow)

    recruiter_profile = relationship("Recruiter", back_populates="user", uselist=False, cascade="all, delete-orphan")
    candidate_profile = relationship("Candidate", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    company = Column(String(100), default="Acme Technologies")
    title = Column(String(100), default="Senior Technical Recruiter")
    department = Column(String(100), default="Engineering Talent")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recruiter_profile")
    interviews = relationship("Interview", back_populates="recruiter")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False, index=True)
    job_role = Column(String(100), nullable=False)
    applied_role = Column(String(100), nullable=True)
    experience_level = Column(String(50), nullable=False)  # Junior, Mid-Level, Senior, Lead
    skills = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="candidate_profile")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")


class QuestionBankItem(Base):
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    question_text = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False, index=True)  # basic, intermediate, advanced
    job_role = Column(String(100), nullable=False, default="General Software Engineer")
    question_type = Column(String(50), default="Technical")  # Technical, Conceptual, Scenario-based, Problem-solving, Behavioral
    target_concept = Column(String(150), nullable=True)
    expected_key_points = Column(JSON, default=list)
    created_by_recruiter_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), default="Technical Assessment")
    description = Column(Text, nullable=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    topics = Column(JSON, default=list)  # list of topics
    difficulty_range = Column(String(50), default="all")  # beginner, intermediate, advanced, all
    total_questions = Column(Integer, default=5)
    duration_minutes = Column(Integer, default=30)
    adaptive_mode = Column(String(20), default="enabled")  # enabled, disabled
    allow_followups = Column(Integer, default=1)
    prevent_repeated = Column(Integer, default=1)
    current_topic = Column(String(100), nullable=False)
    current_question_index = Column(Integer, default=0)
    status = Column(String(20), default="assigned")  # assigned, in_progress, completed
    overall_score = Column(Float, default=0.0)
    weighted_score = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    candidate = relationship("Candidate", back_populates="interviews")
    recruiter = relationship("Recruiter", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestion.question_number")
    knowledge_profiles = relationship("KnowledgeProfile", back_populates="interview", cascade="all, delete-orphan")
    report = relationship("FinalReport", back_populates="interview", uselist=False, cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)  # basic, intermediate, advanced
    target_concept = Column(String(150), nullable=True)
    question_type = Column(String(50), default="Technical")
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False, unique=True)
    candidate_answer = Column(Text, nullable=False)
    score = Column(Float, default=0.0)  # 0.0 - 10.0
    correctness = Column(String(30), nullable=False)  # correct, partially_correct, incorrect
    understanding_level = Column(String(20), nullable=False)  # strong, moderate, partial, weak
    relevant_concepts_identified = Column(JSON, default=list)
    missing_or_misunderstood_concepts = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    knowledge_diagnosis = Column(String(100), nullable=True)
    recommended_strategy = Column(Text, nullable=True)
    adaptive_decision = Column(JSON, default=dict)  # action, next_difficulty, next_topic, reason
    timestamp = Column(DateTime, default=datetime.utcnow)

    question = relationship("InterviewQuestion", back_populates="answer")


class KnowledgeProfile(Base):
    __tablename__ = "knowledge_profiles"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=True)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=True)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)  # basic, intermediate, advanced
    mastery_score = Column(Float, default=0.0)  # 0 - 100
    level = Column(String(30), default="Not demonstrated")  # Strong, Moderate, Partial, Weak, Not demonstrated
    demonstrated_concepts = Column(JSON, default=list)
    missing_concepts = Column(JSON, default=list)
    attempt_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interview = relationship("Interview", back_populates="knowledge_profiles")


class FinalReport(Base):
    __tablename__ = "final_reports"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False, unique=True)
    overall_score = Column(Float, nullable=False)
    weighted_score = Column(Float, nullable=False)
    hiring_recommendation = Column(String(50), nullable=False)
    recommendation_reasoning = Column(Text, nullable=True)
    overall_summary = Column(Text, nullable=True)
    depth_analysis = Column(Text, nullable=True)
    strengths = Column(JSON, default=list)
    areas_for_improvement = Column(JSON, default=list)
    topic_breakdown = Column(JSON, default=dict)
    difficulty_breakdown = Column(JSON, default=dict)
    demonstrated_concepts = Column(JSON, default=list)
    missing_concepts = Column(JSON, default=list)
    transcript = Column(JSON, default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="report")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(20), nullable=False)  # candidate or recruiter
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # interview_assigned, interview_completed, report_ready, reminder
    link = Column(String(255), nullable=True)
    read = Column(Integer, default=0)  # 0 for unread, 1 for read
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
