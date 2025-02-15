from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from api.auth.schemas import Token
from api.auth.services.AuthExceptionService import AuthExceptionService
from api.auth.services.AuthService import AuthService
from db.session import get_session


login_router = APIRouter()


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
        AuthExceptionService.unauthorized_exception("Could not validate credentials")

    access_token = await AuthService.create_access_token_from_refresh(refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}
