from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.core.exceptions import AgentUnavailableError
from app.core.logging import get_logger
from app.services.activity_service import ActivityLog
from app.services.identity import agent_user_id_for

logger = get_logger("app.agent")

Invoker = Callable[..., dict[str, Any]]


def _default_invoker() -> Invoker:
    # Imported lazily: langgraph/langchain are heavy and need GROQ_API_KEY.
    from agent.agent.graph import invoke_agent

    return invoke_agent


class AgentService:
    def __init__(
        self,
        activity: ActivityLog,
        settings: Settings,
        invoker: Invoker | None = None,
    ) -> None:
        self._activity = activity
        self._settings = settings
        self._invoker = invoker

    def handle_message(
        self, user: dict[str, Any], message: str, conversation_id: str | None
    ) -> dict[str, Any]:
        try:
            invoke = self._invoker or _default_invoker()
            result = invoke(
                message,
                user_role=user["role"],
                user_id=agent_user_id_for(user),
                conversation_id=conversation_id,
            )
        except Exception as exc:
            logger.exception("Agent invocation failed")
            self._activity.record("Agent error", str(exc)[:200], "error")
            detail = (
                f"Agent error: {type(exc).__name__}: {exc}"
                if self._settings.debug
                else None
            )
            raise AgentUnavailableError(detail) from exc

        executed = result.get("action_executed")
        if executed == "create_order":
            self._activity.record(
                "Task created",
                f"Agent created {result.get('last_order_id') or 'an order'} from chat",
            )
        else:
            self._activity.record("Agent", message[:120])

        requires_confirmation = result.get("requires_confirmation", False)
        return {
            "reply": result["message"],
            "status": (
                "pending_approval"
                if requires_confirmation
                else ("confirmed" if executed else "ready")
            ),
            "intent": executed or "agent_message",
            "conversation_id": result.get("conversation_id"),
            "requires_confirmation": requires_confirmation,
            "pending_order": result.get("pending_order"),
            "order_id": result.get("last_order_id"),
        }
