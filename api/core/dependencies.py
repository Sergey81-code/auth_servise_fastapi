from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from api.core.exceptions import AppExceptions
from api.v1.users.actions import get_user_by_email_action
from db.session import async_session
from utils.jwt import JWT
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")

async def get_session():
    """Dependency for getting async session"""
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()



async def get_current_user_from_access_token(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    payload = await JWT.decode_jwt_token(token, "access")
    email: str = payload.get("sub")
    user = await get_user_by_email_action(email=email, session=session)
    if user is None:
        AppExceptions.unauthorized_exception("Could not validate credentials")
    return user
