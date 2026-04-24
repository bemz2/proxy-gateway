from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.proxy import (
    ActivationRequest,
    ActivationResponse,
    DisconnectRequest,
    ProxyStatusResponse,
)
from app.services.proxy import activate_key, disconnect_proxy, get_user_status


router = APIRouter()


@router.post("/activate-key", response_model=ActivationResponse)
def activate_proxy_key(
    payload: ActivationRequest,
    db: Session = Depends(get_db),
) -> ActivationResponse:
    return activate_key(db=db, activation_key=payload.activation_key)


@router.post("/disconnect", status_code=status.HTTP_200_OK)
def disconnect_from_proxy(
    payload: DisconnectRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    disconnect_proxy(db=db, user_id=payload.user_id)
    return {"detail": "Proxy released"}


@router.get("/status/{user_id}", response_model=ProxyStatusResponse)
def proxy_status(user_id: int, token: str = Query(...)) -> ProxyStatusResponse:
    return get_user_status(user_id=user_id, ws_token=token)
