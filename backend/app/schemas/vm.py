from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Protocol(str, Enum):
    SOCKS5 = "socks5"
    HTTP = "http"
    HTTPS = "https"


class VirtualMachineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    protocol: Protocol
    is_active: bool = True


class VirtualMachineResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    host: str
    port: int
    protocol: str
    is_active: bool
    current_user_id: int | None
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime
