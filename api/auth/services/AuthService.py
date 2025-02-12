from datetime import timedelta

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from api.auth.services.AuthExceptionService import AuthExceptionService
from api.auth.services.JWTService import JWTService
from api.users.actions import get_user_by_email_action
from db.models import User
from db.session import get_session
from utils.hashing import Hasher


class AuthService:

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")

    def __init__(self, user: User, session: AsyncSession):
        self.user = user
        self.session = session

    @classmethod
    async def create(cls, email: str, password: str, session: AsyncSession):
        user = await cls._authenticate_user(email, password, session)
        if not user:
            AuthExceptionService.unauthorized_exception(
                "Incorrect username or password"
            )
        return cls(user, session)

    @staticmethod
    async def _authenticate_user(
        email: str, password: str, session: AsyncSession
    ) -> User | None:
        user = await get_user_by_email_action(email, session)
        if user is not None:
            if not Hasher.verify_password(password, user.hashed_password):
                return None
        return user

    async def create_access_token(self):
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await JWTService.create_jwt_token(
            data={"sub": self.user.email, "other_custom_data": [1, 2, 3, 4]},
            token_type="access",
            expires_delta=access_token_expires,
        )
        return access_token

    async def create_refresh_token(self):
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = await JWTService.create_jwt_token(
            data={"sub": self.user.email, "other_custom_data": [1, 2, 3, 4]},
            token_type="refresh",
            expires_delta=refresh_token_expires,
        )
        return refresh_token

    @staticmethod
    async def create_access_token_from_refresh(refresh_token: str):
        payload = await JWTService.decode_jwt_token(refresh_token, "refresh")
        email: str = payload.get("sub")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await JWTService.create_jwt_token(
            data={"sub": email, "other_custom_data": [1, 2, 3, 4]},
            token_type="access",
            expires_delta=access_token_expires,
        )
        return access_token

    @staticmethod
    async def get_current_user_from_access_token(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
    ):
        payload = await JWTService.decode_jwt_token(token, "access")
        email: str = payload.get("sub")
        user = await get_user_by_email_action(email=email, session=session)
        if user is None:
            AuthExceptionService.credentials_exception("Could not validate credentials")
        return user
