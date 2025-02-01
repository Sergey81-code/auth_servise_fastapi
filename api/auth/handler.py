from datetime import timedelta

from api.users.models import ShowUser
from db.models import User
import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.actions import _authenticate_user, _create_access_token, _get_current_user_from_token
from api.auth.models import Token
from db.session import get_db


login_router = APIRouter()


@login_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await _authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await _create_access_token(
        data={"sub": user.email, "other_custom_data": [1,2,3,4]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
