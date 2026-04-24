from fastapi import APIRouter

from app.api.routes import auth, profile, proxy, vm, websocket


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
api_router.include_router(vm.router, prefix="/vms", tags=["virtual-machines"])
api_router.include_router(websocket.router, tags=["websocket"])
