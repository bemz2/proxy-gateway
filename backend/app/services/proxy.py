import asyncio
import contextlib
import re
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, WebSocket, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User
from app.models.virtual_machine import VirtualMachine
from app.schemas.proxy import ActivationResponse, AllocatedVm, ProxyStatusResponse

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}
        self.ws_tokens: dict[int, str] = {}
        self.statuses: dict[int, ProxyStatusResponse] = {}
        self.heartbeat_tasks: dict[int, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: int, token: str) -> None:
        expected_token = self.ws_tokens.get(user_id)
        if not expected_token or expected_token != token:
            await websocket.close(code=1008, reason="Invalid websocket token")
            return

        await websocket.accept()
        self.active_connections[user_id] = websocket
        await self.send_current_status(user_id)
        self.heartbeat_tasks[user_id] = asyncio.create_task(self._heartbeat_loop(user_id))

    async def disconnect(self, user_id: int) -> None:
        self.active_connections.pop(user_id, None)
        task = self.heartbeat_tasks.pop(user_id, None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _heartbeat_loop(self, user_id: int) -> None:
        while user_id in self.active_connections:
            await asyncio.sleep(settings.ws_heartbeat_seconds)
            await self.send_current_status(user_id)

    async def send_current_status(self, user_id: int) -> None:
        websocket = self.active_connections.get(user_id)
        status_payload = self.statuses.get(user_id)
        if websocket and status_payload:
            await websocket.send_json(status_payload.model_dump(mode="json"))

    def store_status(self, user_id: int, status_text: str, message: str, vm_id: int | None = None) -> None:
        self.statuses[user_id] = ProxyStatusResponse(
            user_id=user_id,
            status=status_text,
            message=message,
            vm_id=vm_id,
            updated_at=datetime.now(timezone.utc),
        )

    async def notify(self, user_id: int) -> None:
        if user_id in self.active_connections:
            await self.send_current_status(user_id)

    def issue_ws_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(24)
        self.ws_tokens[user_id] = token
        return token


connection_manager = ConnectionManager()


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _normalize_activation_key(raw_key: str) -> str:
    # Clipboard pastes can include spaces, line breaks, or zero-width characters.
    collapsed = re.sub(r"[\s\u200b\u200c\u200d\ufeff]+", "", raw_key).lower()
    if re.fullmatch(rf"[0-9a-f]{{{settings.activation_key_length}}}", collapsed):
        return collapsed

    match = re.search(rf"([0-9a-fA-F]{{{settings.activation_key_length}}})", raw_key)
    return match.group(1).lower() if match else collapsed


def _find_allocatable_vm() -> Select[tuple[VirtualMachine]]:
    return (
        select(VirtualMachine)
        .where(VirtualMachine.is_active.is_(True), VirtualMachine.current_user_id.is_(None))
        .order_by(VirtualMachine.id.asc())
        .with_for_update()
    )


def activate_key(db: Session, activation_key: str) -> ActivationResponse:
    normalized_key = _normalize_activation_key(activation_key)
    logger.info(f"Activation attempt with key: {normalized_key[:8]}...")
    
    user = db.scalar(
        select(User)
        .where(User.activation_key == normalized_key)
        .with_for_update()
    )
    if not user:
        logger.warning(f"Invalid activation key attempted: {normalized_key[:8]}...")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ключ активации недействителен")
    if not user.is_active:
        logger.warning(f"Inactive user {user.id} attempted activation")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь деактивирован")
    if user.activation_key_expires and _as_utc(user.activation_key_expires) < datetime.now(timezone.utc):
        logger.warning(f"Expired key used by user {user.id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия ключа истек")

    vm = db.scalar(_find_allocatable_vm())
    if not vm:
        logger.warning(f"No free VMs available for user {user.id}")
        connection_manager.store_status(
            user_id=user.id,
            status_text="no_free_vms",
            message="Все прокси-серверы заняты",
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Все прокси-серверы заняты")

    vm.current_user_id = user.id
    vm.last_used_at = datetime.now(timezone.utc)
    user.activation_key = None
    user.activation_key_expires = None
    db.add_all([user, vm])
    db.commit()
    db.refresh(vm)
    
    logger.info(f"User {user.id} successfully allocated VM {vm.id} ({vm.name})")
    
    ws_token = connection_manager.issue_ws_token(user.id)
    connection_manager.store_status(
        user_id=user.id,
        status_text="connected",
        message="Прокси успешно выделен",
        vm_id=vm.id,
    )

    return ActivationResponse(
        status="connected",
        user_id=user.id,
        ws_token=ws_token,
        vm=AllocatedVm.model_validate(vm),
        message="Прокси успешно выделен",
    )


def disconnect_proxy(db: Session, user_id: int) -> None:
    vm = db.scalar(select(VirtualMachine).where(VirtualMachine.current_user_id == user_id))
    if not vm:
        logger.warning(f"User {user_id} attempted to disconnect but has no active proxy")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="У пользователя нет активного прокси")

    logger.info(f"User {user_id} disconnecting from VM {vm.id} ({vm.name})")
    vm.current_user_id = None
    db.add(vm)
    db.commit()
    connection_manager.store_status(
        user_id=user_id,
        status_text="disconnected",
        message="Прокси освобожден",
    )


def get_user_status(user_id: int, ws_token: str) -> ProxyStatusResponse:
    expected_token = connection_manager.ws_tokens.get(user_id)
    if not expected_token or expected_token != ws_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен WebSocket")

    status_payload = connection_manager.statuses.get(user_id)
    if not status_payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не найден")
    return status_payload
