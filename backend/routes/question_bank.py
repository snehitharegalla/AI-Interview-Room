"""
Question Bank Management Routes.

Provides endpoints for recruiters to search, filter, create, edit, delete,
duplicate, and preview questions across various categories:
- Technical
- Conceptual
- Scenario-based
- Problem-solving
- Behavioral
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.database import get_db
from backend.models import QuestionBankItem, User
from backend.schemas import (
    QuestionBankItemCreate,
    QuestionBankItemUpdate,
    QuestionBankItemResponse
)
from backend.security import get_optional_user

router = APIRouter(tags=["Question Bank"])


@router.get("", response_model=List[QuestionBankItemResponse])
def list_question_bank(
    search: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    job_role: Optional[str] = None,
    question_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Search and filter questions by topic, difficulty, role, and type.
    """
    query = db.query(QuestionBankItem)

    if topic and topic.lower() != "all":
        query = query.filter(QuestionBankItem.topic.ilike(f"%{topic}%"))

    if difficulty and difficulty.lower() != "all":
        query = query.filter(QuestionBankItem.difficulty == difficulty.lower())

    if job_role and job_role.lower() != "all":
        query = query.filter(QuestionBankItem.job_role.ilike(f"%{job_role}%"))

    if question_type and question_type.lower() != "all":
        query = query.filter(QuestionBankItem.question_type.ilike(f"%{question_type}%"))

    items = query.order_by(QuestionBankItem.created_at.desc()).all()

    if search:
        s = search.lower()
        items = [
            item for item in items
            if s in item.title.lower() or s in item.question_text.lower() or s in (item.target_concept or "").lower()
        ]

    return items


@router.post("", response_model=QuestionBankItemResponse, status_code=status.HTTP_201_CREATED)
def create_question_bank_item(
    item_in: QuestionBankItemCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Creates a new question item in the recruiter question bank.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    new_item = QuestionBankItem(
        title=item_in.title.strip(),
        question_text=item_in.question_text.strip(),
        topic=item_in.topic.strip(),
        difficulty=item_in.difficulty.strip().lower(),
        job_role=item_in.job_role.strip(),
        question_type=item_in.question_type.strip(),
        target_concept=item_in.target_concept,
        expected_key_points=item_in.expected_key_points,
        created_at=datetime.utcnow()
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get("/{item_id}", response_model=QuestionBankItemResponse)
def get_question_bank_item(item_id: int, db: Session = Depends(get_db)):
    """
    Returns a single question bank item for preview or inspection.
    """
    item = db.query(QuestionBankItem).filter(QuestionBankItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question bank item not found.")
    return item


@router.put("/{item_id}", response_model=QuestionBankItemResponse)
def update_question_bank_item(
    item_id: int,
    item_in: QuestionBankItemUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Updates an existing question item in the Question Bank.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    item = db.query(QuestionBankItem).filter(QuestionBankItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question bank item not found.")

    if item_in.title is not None:
        item.title = item_in.title.strip()
    if item_in.question_text is not None:
        item.question_text = item_in.question_text.strip()
    if item_in.topic is not None:
        item.topic = item_in.topic.strip()
    if item_in.difficulty is not None:
        item.difficulty = item_in.difficulty.strip().lower()
    if item_in.job_role is not None:
        item.job_role = item_in.job_role.strip()
    if item_in.question_type is not None:
        item.question_type = item_in.question_type.strip()
    if item_in.target_concept is not None:
        item.target_concept = item_in.target_concept
    if item_in.expected_key_points is not None:
        item.expected_key_points = item_in.expected_key_points

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
def delete_question_bank_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Removes a question item from the Question Bank.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    item = db.query(QuestionBankItem).filter(QuestionBankItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question bank item not found.")

    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Question successfully deleted."}


@router.post("/{item_id}/duplicate", response_model=QuestionBankItemResponse)
def duplicate_question_bank_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Duplicates an existing question to speed up variation creation.
    """
    if current_user and current_user.role == "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Recruiter privileges are required."
        )

    item = db.query(QuestionBankItem).filter(QuestionBankItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question bank item not found.")

    duplicated = QuestionBankItem(
        title=f"{item.title} (Copy)",
        question_text=item.question_text,
        topic=item.topic,
        difficulty=item.difficulty,
        job_role=item.job_role,
        question_type=item.question_type,
        target_concept=item.target_concept,
        expected_key_points=list(item.expected_key_points or []),
        created_at=datetime.utcnow()
    )
    db.add(duplicated)
    db.commit()
    db.refresh(duplicated)
    return duplicated
