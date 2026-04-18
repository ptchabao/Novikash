from fastapi import Request, APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.models import User, Notification
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class NotificationRead(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

@router.get("/", response_model=List[NotificationRead])
def get_notifications(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    notifications = session.exec(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    ).all()
    return notifications

@router.post("/{notification_id}/read")
def mark_read(notification_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    notification = session.exec(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == current_user.id)
    ).first()
    if notification:
        notification.is_read = True
        session.add(notification)
        session.commit()
    return {"status": "ok"}
