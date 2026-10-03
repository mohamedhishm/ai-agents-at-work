from __future__ import annotations

from typing import Any


class InventoryService:

    def __init__(self, store: Any | None = None) -> None:
        self._store = store

    def _get_store(self):
        if self._store is None:
            from eldockor.store.file_store import FileStore

            self._store = FileStore()
        return self._store

    def summary(self):
        return self._get_store().get_inventory_summary()

    def low_stock(self):
        return self._get_store().get_low_stock_items()
