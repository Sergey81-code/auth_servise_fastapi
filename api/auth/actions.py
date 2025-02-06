import datetime

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from db.dals import UserDAL
from db.models import User
from db.session import get_session
from utils.hashing import Hasher


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")


async def _get_user_by_email_for_auth(email: str, session: AsyncSession) -> User | None:
    async with session.begin():
        user_dal = UserDAL(session)
        user = await user_dal.get_user_by_email(email=email)
        return user


async def _authenticate_user(
    email: str, password: str, session: AsyncSession
) -> User | None:
    user = await _get_user_by_email_for_auth(email, session)
    if user is not None:
        if not Hasher.verify_password(password, user.hashed_password):
            return None
    return user


async def _create_jwt_token(
    data: dict, token_type: str, expires_delta: datetime.timedelta | None = None
):
    token_key, token_time = (
        (settings.SECRET_KEY_FOR_ACCESS, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if token_type == "access"
        else (settings.SECRET_KEY_FOR_REFRESH, settings.REFRESH_TOKEN_EXPIRE_DAYS*24*60)
    )
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=token_time
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, token_key, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def _get_current_user_from_token(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY_FOR_ACCESS, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        print("username/email extracted is ", email)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await _get_user_by_email_for_auth(email=email, session=session)
    if user is None:
        raise credentials_exception
    return user
