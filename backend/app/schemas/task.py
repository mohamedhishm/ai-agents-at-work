from __future__ import annotations

from pydantic import BaseModel


class TaskView(BaseModel):
    id: int
    order_id: str
    title: str
    customer: str
    customer_id: str | None = None
    amount: int | float = 0
    status: str
    eta: str
    location: str
    created_at: str = ""


class ApprovalRequest(BaseModel):
    approved: bool
