"""In-memory activity feed shown on the admin dashboard."""

from __future__ import annotations

import itertools
import threading
from collections import deque
from typing import Any

from app.core.constants import ACTIVITY_LOG_LIMIT


class ActivityLog:
    def __init__(self, limit: int = ACTIVITY_LOG_LIMIT) -> None:
        self._items: deque[dict[str, Any]] = deque(maxlen=limit)
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self.record("System", "FastAPI backend connected to LangGraph agent")

    def record(self, kind: str, detail: str, status: str = "done") -> None:
        with self._lock:
            self._items.appendleft(
                {"id": next(self._ids), "type": kind, "detail": detail, "status": status}
            )

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._items)


# Process-wide singleton (swap for a DB-backed implementation later).
activity_log = ActivityLog()
