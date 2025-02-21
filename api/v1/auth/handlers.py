from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.dependencies import get_session
from api.core.exceptions import AppExceptions
from api.v1.auth.schemas import Token
from api.v1.auth.services.AuthService import AuthService


login_router = APIRouter()

settings = get_settings()


@login_router.post("/", response_model=Token)
async def login_for_get_tokens(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    auth_service = await AuthService.create(
        form_data.username, form_data.password, session
    )

    access_token = await auth_service.create_access_token()
    refresh_token = await auth_service.create_refresh_token()

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Not only https. Turn off in realise
        samesite="Strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@login_router.post("/token", response_model=Token)
async def create_new_access_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        AppExceptions.unauthorized_exception("Could not validate credentials")

    access_token = await AuthService.create_access_token_from_refresh(refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}
