from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import ChangePasswordRequest, UserResponse
from app.services.auth import get_current_user
from app.services.user import change_password, refresh_activation_key


router = APIRouter()


@router.get("", response_model=UserResponse)
def get_profile(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/refresh-key", response_model=UserResponse, status_code=status.HTTP_200_OK)
def rotate_key(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserResponse:
    user = refresh_activation_key(db=db, user=current_user)
    return UserResponse.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    change_password(db=db, user=current_user, payload=payload)
