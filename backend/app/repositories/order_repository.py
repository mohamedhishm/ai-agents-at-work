from __future__ import annotations

from pathlib import Path
from typing import Any

from app.repositories.json_file import JsonFile

Order = dict[str, Any]


class OrderRepository:

    def __init__(self, path: Path) -> None:
        self._file = JsonFile(path)

    def list(self) -> list[Order]:
        return self._file.read()

    def get(self, order_id: str) -> Order | None:
        return next((o for o in self.list() if o.get("order_id") == order_id), None)

    def set_status(self, order_id: str, status: str) -> Order | None:
        with self._file.lock:
            orders = self._file.read()
            target = next((o for o in orders if o.get("order_id") == order_id), None)
            if target is None:
                return None
            target["status"] = status
            self._file.write(orders)
            return target
