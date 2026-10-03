from fastapi import APIRouter

from app.api.routes import agents, auth, inventory, system, tasks

api_router = APIRouter()
for module in (system, auth, agents, tasks, inventory):
    api_router.include_router(module.router)
