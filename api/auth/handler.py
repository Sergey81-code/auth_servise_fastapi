from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from api.auth.actions import _authenticate_user
from api.auth.actions import _create_access_token
from api.auth.actions import _create_refresh_token
from api.auth.models import Token
from db.session import get_db


login_router = APIRouter()


@login_router.post("/", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await _authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await _create_access_token(
        data={"sub": user.email, "other_custom_data": [1, 2, 3, 4]},
        expires_delta=access_token_expires,
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = await _create_refresh_token(
        data={"sub": user.email, "other_custom_data": [1, 2, 3, 4]},
        expires_delta=refresh_token_expires,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Not only https. Turn off in realise
        samesite="Strict",
        max_age=60 * 60 * 24 * 10,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@login_router.post("/token", response_model=Token)
async def create_new_access_token(request: Request, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        refresh_token = request.cookies.get("refresh_token")
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY_FOR_REFRESH,
            algorithms=[settings.ALGORITHM],
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await _create_access_token(
            data={"sub": email, "other_custom_data": [1, 2, 3, 4]},
            expires_delta=access_token_expires,
        )
    except (JWTError, TypeError, AttributeError):
        raise credentials_exception
    return {"access_token": access_token, "token_type": "bearer"}
