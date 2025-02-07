from logging import getLogger
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.services.AuthService import AuthService
from api.users.actions import activate_user_action
from api.users.actions import create_new_user_action
from api.users.actions import delete_user_action
from api.users.actions import get_user_by_id_action
from api.users.actions import update_user_action
from api.users.models import ActivateUserResponse
from api.users.models import DeleteUserResponse
from api.users.models import ShowUser
from api.users.models import UpdatedUserResponse
from api.users.models import UpdateUserRequest
from api.users.models import UserCreate
from db.models import User
from db.session import get_session

logger = getLogger(__name__)

user_router = APIRouter()


@user_router.post("/", response_model=ShowUser)
async def create_user(
    body: UserCreate, session: AsyncSession = Depends(get_session)
) -> ShowUser:
    try:
        user = await create_new_user_action(body, session)
        return ShowUser(
            user_id=user.user_id,
            name=user.name,
            surname=user.surname,
            email=user.email,
            is_active=user.is_active,
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.delete("/", response_model=DeleteUserResponse)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
    session: AsyncSession = Depends(get_session),
) -> DeleteUserResponse:
    deleted_user_id = await delete_user_action(user_id, session)
    if deleted_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return DeleteUserResponse(deleted_user_id=deleted_user_id)


@user_router.post("/activate", response_model=ActivateUserResponse)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
    session: AsyncSession = Depends(get_session),
) -> ActivateUserResponse:
    activated_user_id = await activate_user_action(user_id, session)
    if activated_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return ActivateUserResponse(activated_user_id=activated_user_id)


@user_router.get("/", response_model=ShowUser)
async def get_user_by_id(
    user_id: UUID,
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
    session: AsyncSession = Depends(get_session),
) -> ShowUser:
    user = await get_user_by_id_action(user_id, session)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return ShowUser(
        user_id=user.user_id,
        name=user.name,
        surname=user.surname,
        email=user.email,
        is_active=user.is_active,
    )


@user_router.patch("/", response_model=UpdatedUserResponse)
async def update_user_by_id(
    user_id: UUID,
    body: UpdateUserRequest,
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
    session: AsyncSession = Depends(get_session),
) -> UpdatedUserResponse:
    try:
        updated_user_id = await update_user_action(user_id, body, session)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UpdatedUserResponse(updated_user_id=updated_user_id)
