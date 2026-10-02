from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

_registry_lock = threading.Lock()
_locks: dict[Path, threading.RLock] = {}


def _lock_for(path: Path) -> threading.RLock:
    # One lock per file, shared across repository instances (created per request).
    with _registry_lock:
        return _locks.setdefault(path.resolve(), threading.RLock())


class JsonFile:
    def __init__(self, path: Path, default_factory: Callable[[], Any] = list) -> None:
        self.path = Path(path)
        self._default_factory = default_factory
        self.lock = _lock_for(self.path)

    def read(self) -> Any:
        if not self.path.exists():
            return self._default_factory()
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, value: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp file then rename, so readers never see a partial file.
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(value, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
