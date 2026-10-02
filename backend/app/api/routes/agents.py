from fastapi import APIRouter

from app.api.deps import ActivityDep, AdminUser, AgentServiceDep, CurrentUser
from app.schemas.agent import ActivityItem, MessageRequest, MessageResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/message", response_model=MessageResponse)
def send_message(body: MessageRequest, user: CurrentUser, agent: AgentServiceDep):
    return agent.handle_message(user, body.message, body.conversation_id)


@router.get("/activity", response_model=list[ActivityItem])
def activity(_: AdminUser, log: ActivityDep):
    return log.list()
