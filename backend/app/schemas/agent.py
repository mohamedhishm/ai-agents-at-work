from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: str | None = None


class MessageResponse(BaseModel):
    reply: str
    status: str
    intent: str
    conversation_id: str | None = None
    requires_confirmation: bool = False
    pending_order: dict[str, Any] | None = None
    order_id: str | None = None


class ActivityItem(BaseModel):
    id: int
    type: str
    detail: str
    status: str
