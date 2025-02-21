from fastapi import APIRouter
from api.v1.auth.handlers import login_router
from api.v1.users.handlers import user_router

router = APIRouter()

api_v1 = APIRouter(prefix="/v1")

api_v1.include_router(user_router, prefix="/users", tags=["users"])
api_v1.include_router(login_router, prefix="/login", tags=["login"])

router.include_router(api_v1)