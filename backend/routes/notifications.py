"""
Notification Routes.

Handles notifications for candidate reminders, assignments, and recruiter alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import Notification, User
from backend.schemas import NotificationResponse
from backend.security import get_optional_user

router = APIRouter(tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns notifications for the current user or filtered by role.
    """
    query = db.query(Notification)

    if current_user:
        query = query.filter(Notification.user_id == current_user.id)
    elif role:
        query = query.filter(Notification.role == role.strip().lower())

    return query.order_by(Notification.created_at.desc()).limit(20).all()


@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """
    Marks a notification as read.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.read = 1
    db.commit()
    return {"status": "success", "id": notification_id, "read": 1}


@router.post("/read-all")
def mark_all_notifications_read(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Marks all notifications as read.
    """
    query = db.query(Notification)
    if current_user:
        query = query.filter(Notification.user_id == current_user.id)
    elif role:
        query = query.filter(Notification.role == role.strip().lower())

    query.update({Notification.read: 1}, synchronize_session=False)
    db.commit()
    return {"status": "success", "message": "All notifications marked as read."}
