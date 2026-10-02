from __future__ import annotations

from typing import Any

from app.core.constants import AGENT_ADMIN_ID, AGENT_CUSTOMER_ID, Role


def agent_user_id_for(user: dict[str, Any]) -> str:
    # TODO: derive from a real customer profile once one exists.
    return AGENT_ADMIN_ID if user["role"] == Role.ADMIN.value else AGENT_CUSTOMER_ID
