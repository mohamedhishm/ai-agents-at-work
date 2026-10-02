from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.constants import Role
from app.core.exceptions import AuthenticationError, BadRequestError
from app.core.security import create_access_token, decode_access_token, verify_password
from app.repositories.user_repository import UserRepository

User = dict[str, Any]


def public_user(user: User) -> User:
    return {k: v for k, v in user.items() if k != "password"}


class AuthService:
    def __init__(self, users: UserRepository, settings: Settings) -> None:
        self._users = users
        self._settings = settings

    def _issue(self, user: User) -> dict[str, Any]:
        token = create_access_token(
            {"sub": user["id"], "email": user["email"], "role": user["role"]},
            secret=self._settings.jwt_secret,
            ttl_seconds=self._settings.token_ttl_seconds,
        )
        return {"token": token, "user": public_user(user)}

    def login(self, email: str, password: str, role: str | None = None) -> dict[str, Any]:
        user = self._users.get_by_email(email)
        if not user or not verify_password(password, user["password"]):
            raise AuthenticationError("Invalid email or password.")
        if role and user["role"] != role:
            raise BadRequestError("This account does not match the selected role.")
        return self._issue(user)

    def register(self, name: str, email: str, password: str) -> dict[str, Any]:
        user = self._users.create(
            name=name.strip(), email=email, password=password, role=Role.CUSTOMER
        )
        return self._issue(user)

    def user_from_token(self, token: str) -> User:
        payload = decode_access_token(token, secret=self._settings.jwt_secret)
        user = self._users.get_by_email(payload["email"])
        if not user:
            raise AuthenticationError("User no longer exists")
        return public_user(user)
