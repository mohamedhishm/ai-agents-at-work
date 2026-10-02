from fastapi import APIRouter

from app.api.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, auth: AuthServiceDep):
    return auth.login(body.email, body.password, body.role)


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, auth: AuthServiceDep):
    return auth.register(body.name, body.email, body.password)


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser):
    return user
