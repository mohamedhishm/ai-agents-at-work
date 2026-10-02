from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.constants import Role
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityLog, activity_log
from app.services.agent_service import AgentService
from app.services.auth_service import AuthService
from app.services.inventory_service import InventoryService
from app.services.task_service import TaskService

bearer = HTTPBearer(auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_activity_log() -> ActivityLog:
    return activity_log


ActivityDep = Annotated[ActivityLog, Depends(get_activity_log)]


def get_auth_service(settings: SettingsDep) -> AuthService:
    return AuthService(UserRepository(settings.users_file), settings)


def get_task_service(settings: SettingsDep, activity: ActivityDep) -> TaskService:
    return TaskService(OrderRepository(settings.orders_file), activity)


def get_agent_service(settings: SettingsDep, activity: ActivityDep) -> AgentService:
    return AgentService(activity, settings)


def get_inventory_service() -> InventoryService:
    return InventoryService()


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
InventoryServiceDep = Annotated[InventoryService, Depends(get_inventory_service)]


def get_current_user(
    auth: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, Any]:
    if not credentials:
        raise AuthenticationError("Authentication required")
    return auth.user_from_token(credentials.credentials)


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def require_admin(user: CurrentUser) -> dict[str, Any]:
    if user["role"] != Role.ADMIN.value:
        raise PermissionDeniedError("Admin access required")
    return user


AdminUser = Annotated[dict[str, Any], Depends(require_admin)]
