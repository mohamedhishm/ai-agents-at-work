from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any

from app.core.exceptions import AuthenticationError


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body: str, secret: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def create_access_token(
    claims: dict[str, Any], *, secret: str, ttl_seconds: int
) -> str:
    payload = {
        **claims,
        "exp": int(time.time()) + ttl_seconds,
        "jti": uuid.uuid4().hex,
    }
    body = _b64e(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    )
    return f"{body}.{_sign(body, secret)}"


def decode_access_token(token: str, *, secret: str) -> dict[str, Any]:
    try:
        body, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body, secret)):
            raise ValueError("bad signature")
        payload = json.loads(_b64d(body).decode())
        if payload["exp"] < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise AuthenticationError("Invalid or expired token") from exc


def verify_password(plain: str, stored: str) -> bool:
    """Constant-time comparison.

    NOTE: the demo data stores plaintext passwords. Replace the body with
    ``passlib``/``bcrypt`` verification when moving to a real user store.
    """
    return hmac.compare_digest(plain.encode(), stored.encode())
