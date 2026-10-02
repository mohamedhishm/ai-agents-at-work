from __future__ import annotations

from typing import Any

from app.core.constants import Role
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.repositories.order_repository import OrderRepository
from app.services.activity_service import ActivityLog
from app.services.identity import agent_user_id_for
from app.services.task_presenter import order_id_from_number, to_task_view


class TaskService:
    def __init__(self, orders: OrderRepository, activity: ActivityLog) -> None:
        self._orders = orders
        self._activity = activity

    def list_for(self, user: dict[str, Any]) -> list[dict[str, Any]]:
        orders = self._orders.list()
        if user["role"] != Role.ADMIN.value:
            owner = agent_user_id_for(user)
            orders = [o for o in orders if o.get("customer_id") == owner]
        return [to_task_view(o) for o in reversed(orders)]

    def decide(self, number: int, approved: bool) -> None:
        order_id = order_id_from_number(number)
        status = "processing" if approved else "rejected"
        if self._orders.set_status(order_id, status) is None:
            raise NotFoundError("Order not found")
        self._activity.record(
            "Approval", f"Order #{number} {'approved' if approved else 'rejected'} by admin"
        )

    def cancel(self, number: int, user: dict[str, Any]) -> None:
        order = self._orders.get(order_id_from_number(number))
        if order is None:
            raise NotFoundError("Order not found")
        if user["role"] != Role.ADMIN.value and order.get("customer_id") != agent_user_id_for(user):
            raise PermissionDeniedError("You cannot cancel this order")
        self._orders.set_status(order["order_id"], "cancelled")
        self._activity.record("Cancellation", f"Order #{number} cancelled")
