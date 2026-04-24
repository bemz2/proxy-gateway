import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.schemas.user import ChangePasswordRequest
from app.services.security import get_password_hash, verify_password
from app.tasks.email_tasks import send_activation_email_task


def _generate_activation_key() -> str:
    return secrets.token_hex(settings.activation_key_length // 2)


def issue_activation_key(db: Session, user: User) -> User:
    user.activation_key = _generate_activation_key()
    user.activation_key_expires = datetime.now(timezone.utc) + timedelta(hours=settings.activation_key_ttl_hours)
    db.add(user)
    db.flush()
    send_activation_email_task.delay(user.email, user.activation_key)
    return user


def refresh_activation_key(db: Session, user: User) -> User:
    user.activation_key = None
    user.activation_key_expires = None
    db.add(user)
    db.flush()
    issue_activation_key(db=db, user=user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, payload: ChangePasswordRequest) -> None:
    if payload.new_password != payload.new_password_confirmation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.password_hash = get_password_hash(payload.new_password)
    db.add(user)
    db.commit()
