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
from db.session import get_db
from utils.hashing import Hasher


async def _get_user_by_email_for_auth(email: str, db: AsyncSession) -> User | None:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.get_user_by_email(email=email)
            return user


async def _authenticate_user(
    email: str, password: str, db: AsyncSession
) -> User | None:
    user = await _get_user_by_email_for_auth(email, db)
    if user is not None:
        if not Hasher.verify_password(password, user.hashed_password):
            return None
    return user


async def _create_access_token(
    data: dict, expires_delta: datetime.timedelta | None = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY_FOR_ACCESS, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def _create_refresh_token(
    data: dict, expires_delta: datetime.timedelta | None = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY_FOR_REFRESH, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")


async def _get_current_user_from_token(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY_FOR_ACCESS, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        print("username/email extracted is ", username)
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await _get_user_by_email_for_auth(email=username, db=db)
    if user is None:
        raise credentials_exception
    return user
