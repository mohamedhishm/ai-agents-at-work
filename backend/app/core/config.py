from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Ensure PYTHONPATH includes project root for agent module resolution
_project_root = Path(__file__).resolve().parents[3]  # backend/app/core/config.py -> project root
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# <repo>/backend  (app/core/config.py -> parents[2])
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

_INSECURE_DEFAULT_SECRET = "change-me-in-production"


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in os.getenv(name, default).split(",") if x.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_description: str
    environment: str
    debug: bool
    log_level: str
    jwt_secret: str
    token_ttl_seconds: int
    frontend_origins: tuple[str, ...]
    users_file: Path
    orders_file: Path

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


def _load_settings() -> Settings:
    from app import __version__

    settings = Settings(
        app_name="El Doctor AI Backend",
        app_version=__version__,
        app_description=(
            "FastAPI bridge between the Next.js frontend and the existing LangGraph agent."
        ),
        environment=os.getenv("ENVIRONMENT", "development").strip().lower(),
        debug=_bool("DEBUG", False),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        jwt_secret=os.getenv("JWT_SECRET", _INSECURE_DEFAULT_SECRET),
        token_ttl_seconds=int(os.getenv("TOKEN_TTL_SECONDS", "86400")),
        frontend_origins=_csv(
            "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ),
        users_file=Path(os.getenv("USERS_FILE", BASE_DIR / "data" / "users.json")),
        orders_file=Path(
            os.getenv("ORDERS_FILE", BASE_DIR / "eldockor" / "data" / "orders.json")
        ),
    )
    if settings.is_production and settings.jwt_secret == _INSECURE_DEFAULT_SECRET:
        raise RuntimeError("JWT_SECRET must be set when ENVIRONMENT=production")
    return settings


@lru_cache
def get_settings() -> Settings:
    return _load_settings()
