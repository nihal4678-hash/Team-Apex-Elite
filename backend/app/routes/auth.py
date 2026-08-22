from fastapi import APIRouter
from app.models.user import LoginRequest, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=User)
def login(payload: LoginRequest) -> User:
    return User(id="jordan-davis", name="Jordan Davis", email=payload.email, role="Energy manager")
