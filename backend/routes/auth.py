"""
Authentication & User Session Routes.

Provides endpoints for candidate and recruiter registration, login, profile retrieval,
and instant demo logins.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models import User, Recruiter, Candidate, Notification
from backend.schemas import LoginRequest, RegisterRequest, AuthResponse, UserResponse
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new Candidate or Recruiter account with secure password hashing.
    """
    email_clean = request.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 1. Create User
    user = User(
        email=email_clean,
        password_hash=hash_password(request.password),
        full_name=request.full_name.strip(),
        role=request.role.strip().lower(),
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. Create Role Profile
    profile_data = {}
    if user.role == "recruiter":
        recruiter = Recruiter(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
            company=request.company or "Acme Technologies",
            title=request.title or "Technical Recruiter",
            department="Talent Acquisition"
        )
        db.add(recruiter)
        db.commit()
        profile_data = {"company": recruiter.company, "title": recruiter.title}
    else:
        candidate = Candidate(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
            job_role=request.job_role or "Software Engineer",
            applied_role=request.job_role or "Software Engineer",
            experience_level=request.experience_level or "Mid-Level",
            skills=[]
        )
        db.add(candidate)
        db.commit()
        profile_data = {
            "job_role": candidate.job_role,
            "experience_level": candidate.experience_level
        }

    # Add welcome notification
    welcome_notif = Notification(
        user_id=user.id,
        role=user.role,
        title="Welcome to AI Interview Room!",
        message=f"Your {user.role.title()} account has been successfully created. Explore your workspace.",
        type="welcome"
    )
    db.add(welcome_notif)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            profile=profile_data,
            created_at=user.created_at
        )
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates Candidate or Recruiter credentials and returns JWT Bearer token.
    """
    email_clean = request.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials."
        )

    # Optional role check if user specifically logged in from role-locked portal
    if request.role and request.role.strip().lower() != user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account is registered as a {user.role.title()}, not a {request.role.title()}."
        )

    profile_data = {}
    if user.role == "recruiter" and user.recruiter_profile:
        profile_data = {
            "recruiter_id": user.recruiter_profile.id,
            "company": user.recruiter_profile.company,
            "title": user.recruiter_profile.title
        }
    elif user.role == "candidate" and user.candidate_profile:
        profile_data = {
            "candidate_id": user.candidate_profile.id,
            "job_role": user.candidate_profile.job_role,
            "experience_level": user.candidate_profile.experience_level
        }

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            profile=profile_data,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
def get_current_profile(current_user: User = Depends(get_current_user)):
    """
    Returns profile information for current authenticated user.
    """
    profile_data = {}
    if current_user.role == "recruiter" and current_user.recruiter_profile:
        profile_data = {
            "recruiter_id": current_user.recruiter_profile.id,
            "company": current_user.recruiter_profile.company,
            "title": current_user.recruiter_profile.title,
            "department": current_user.recruiter_profile.department
        }
    elif current_user.role == "candidate" and current_user.candidate_profile:
        profile_data = {
            "candidate_id": current_user.candidate_profile.id,
            "job_role": current_user.candidate_profile.job_role,
            "experience_level": current_user.candidate_profile.experience_level,
            "skills": current_user.candidate_profile.skills or []
        }

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        profile=profile_data,
        created_at=current_user.created_at
    )


@router.post("/demo-login", response_model=AuthResponse)
def demo_login(role: str = "recruiter", db: Session = Depends(get_db)):
    """
    Instant demo login helper for evaluation and live walkthroughs.
    role: 'recruiter' (Sarah Jenkins) or 'candidate' (Alex Rivera)
    """
    role_clean = role.strip().lower()
    target_email = "sarah.jenkins@techcorp.io" if role_clean == "recruiter" else "alex.rivera@example.com"

    user = db.query(User).filter(User.email == target_email).first()
    if not user:
        # Fallback to any user matching role
        user = db.query(User).filter(User.role == role_clean).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Demo {role_clean} account not found. Please run seed script first."
        )

    profile_data = {}
    if user.role == "recruiter" and user.recruiter_profile:
        profile_data = {
            "recruiter_id": user.recruiter_profile.id,
            "company": user.recruiter_profile.company,
            "title": user.recruiter_profile.title
        }
    elif user.role == "candidate" and user.candidate_profile:
        profile_data = {
            "candidate_id": user.candidate_profile.id,
            "job_role": user.candidate_profile.job_role,
            "experience_level": user.candidate_profile.experience_level
        }

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            profile=profile_data,
            created_at=user.created_at
        )
    )


@router.post("/forgot-password")
def forgot_password(email_data: dict):
    """
    Password reset simulator.
    """
    email = email_data.get("email", "")
    return {
        "status": "success",
        "message": f"If an account is associated with '{email}', a password reset link has been dispatched."
    }
