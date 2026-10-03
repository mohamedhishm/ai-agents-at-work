from __future__ import annotations

import re
from typing import Any

from app.core.constants import AGENT_CUSTOMER_NAMES

_ETA = {
    "pending": "Awaiting approval",
    "pending_approval": "After approval",
    "confirmed": "Processing",
    "processing": "Processing",
    "shipped": "In transit",
    "delivered": "Delivered",
    "rejected": "Rejected",
    "cancelled": "Cancelled",
    "failed": "Failed",
}

_LOCATION = {
    "pending": "Human approval queue",
    "pending_approval": "Human approval queue",
    "confirmed": "El Doctor main warehouse",
    "processing": "El Doctor main warehouse",
    "shipped": "El Doctor warehouse — Alexandria",
    "delivered": "Delivered to customer",
    "rejected": "Human approval",
    "cancelled": "Order cancelled by customer",
}


def customer_name(customer_id: str | None) -> str:
    return AGENT_CUSTOMER_NAMES.get(customer_id, customer_id or "Customer")


def order_number(order_id: str) -> int:
    return int(re.sub(r"\D", "", order_id) or 0)


def order_id_from_number(number: int) -> str:
    return f"ORD-{number:03d}"


def to_task_view(order: dict[str, Any]) -> dict[str, Any]:
    order_id = order.get("order_id", "")
    items = order.get("items", [])
    title = (
        ", ".join(
            f"{i.get('name') or i.get('product_id')} × {i.get('quantity', 0)}"
            for i in items
        )
        or "Spare-parts request"
    )
    status = order.get("status", "pending")
    return {
        "id": order_number(order_id),
        "order_id": order_id,
        "title": title,
        "customer": customer_name(order.get("customer_id")),
        "customer_id": order.get("customer_id"),
        "amount": order.get("total", 0),
        "status": status,
        "eta": _ETA.get(status, status.replace("_", " ").title()),
        "location": _LOCATION.get(status, "El Doctor operations"),
        "created_at": order.get("created_at", ""),
    }
