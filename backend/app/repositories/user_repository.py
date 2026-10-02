from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.constants import Role
from app.core.exceptions import ConflictError
from app.repositories.json_file import JsonFile

User = dict[str, Any]


class UserRepository:
    def __init__(self, path: Path) -> None:
        self._file = JsonFile(path)

    def list(self) -> list[User]:
        return self._file.read()

    def get_by_email(self, email: str) -> User | None:
        email = email.strip().lower()
        return next((u for u in self.list() if u["email"].lower() == email), None)

    def create(self, *, name: str, email: str, password: str, role: Role) -> User:
        with self._file.lock:
            users = self._file.read()
            if any(u["email"].lower() == email.lower() for u in users):
                raise ConflictError("An account with this email already exists.")
            user = {
                "id": max((u["id"] for u in users), default=0) + 1,
                "name": name,
                "email": email.lower(),
                "password": password,
                "role": role.value,
            }
            users.append(user)
            self._file.write(users)
            return user
