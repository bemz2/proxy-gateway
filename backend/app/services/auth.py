from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserRegister
from app.schemas.user import UserResponse
from app.services.security import get_password_hash, verify_password
from app.services.user import issue_activation_key

logger = get_logger(__name__)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(subject: str) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def register_user(db: Session, payload: UserRegister) -> User:
    if payload.password != payload.password_confirmation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {payload.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    issue_activation_key(db=db, user=user)
    db.commit()
    db.refresh(user)
    logger.info(f"New user registered: {user.email} (ID: {user.id})")
    return user


def login_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {payload.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {user.email} (ID: {user.id})")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    logger.info(f"User logged in: {user.email} (ID: {user.id})")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc

    user = db.get(User, int(user_id)) if user_id else None
    if not user:
        raise credentials_exception
    return user
