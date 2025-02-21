from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import AppExceptions
from utils.jwt import JWT
from api.v1.users.actions import get_user_by_email_action
from db.models import User
from utils.hashing import Hasher


class AuthService:

    def __init__(self, user: User, session: AsyncSession):
        self.user = user
        self.session = session

    @classmethod
    async def create(cls, email: str, password: str, session: AsyncSession):
        user = await cls._authenticate_user(email, password, session)
        if not user:
            AppExceptions.unauthorized_exception(
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
        return await JWT.create_jwt_token(
            data={"sub": self.user.email, "other_custom_data": [1, 2, 3, 4]},
            token_type="access"
        )

    async def create_refresh_token(self):
        return await JWT.create_jwt_token(
            data={"sub": self.user.email, "other_custom_data": [1, 2, 3, 4]},
            token_type="refresh",
        )

    @staticmethod
    async def create_access_token_from_refresh(refresh_token: str):
        payload = await JWT.decode_jwt_token(refresh_token, "refresh")
        email: str = payload.get("sub")
        return await JWT.create_jwt_token(
            data={"sub": email, "other_custom_data": [1, 2, 3, 4]},
            token_type="access",
        )