from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.proxy import connection_manager


router = APIRouter()


@router.websocket("/ws/status/{user_id}")
async def connection_status(websocket: WebSocket, user_id: int, token: str) -> None:
    await connection_manager.connect(websocket=websocket, user_id=user_id, token=token)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await connection_manager.disconnect(user_id=user_id)
