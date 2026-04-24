from datetime import datetime

from pydantic import BaseModel


class ActivationRequest(BaseModel):
    activation_key: str


class AllocatedVm(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    host: str
    port: int
    protocol: str


class ActivationResponse(BaseModel):
    status: str
    user_id: int
    ws_token: str
    vm: AllocatedVm
    message: str


class DisconnectRequest(BaseModel):
    user_id: int


class ProxyStatusResponse(BaseModel):
    user_id: int
    status: str
    message: str
    vm_id: int | None = None
    updated_at: datetime
