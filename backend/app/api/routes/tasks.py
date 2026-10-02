from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, TaskServiceDep
from app.schemas.task import ApprovalRequest, TaskView

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskView])
def list_tasks(user: CurrentUser, tasks: TaskServiceDep):
    return tasks.list_for(user)


@router.post("/{order_id}/approval")
def approval(order_id: int, body: ApprovalRequest, _: AdminUser, tasks: TaskServiceDep):
    tasks.decide(order_id, body.approved)
    return {}


@router.post("/{order_id}/cancel")
def cancel(order_id: int, user: CurrentUser, tasks: TaskServiceDep):
    tasks.cancel(order_id, user)
    return {}
