from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


AGENT_CUSTOMER_ID = "CUST-001"
AGENT_ADMIN_ID = "ADMIN-001"

AGENT_CUSTOMER_NAMES: dict[str, str] = {
    AGENT_CUSTOMER_ID: "Salma Mohamed",
    AGENT_ADMIN_ID: "Nour Hussien",
}

ACTIVITY_LOG_LIMIT = 100
