from logging import getLogger
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.services.AuthService import AuthService
from api.users.actions import activate_user_action, grant_admin_privilege_action, revoke_admin_privilege_action, update_user_action
from api.users.actions import check_user_permissions
from api.users.actions import create_new_user_action
from api.users.actions import delete_user_action
from api.users.actions import fetch_user_or_raise
from api.users.actions import process_user_update_request_action
from api.users.schemas import ActivateUserResponse
from api.users.schemas import DeleteUserResponse
from api.users.schemas import ShowUser
from api.users.schemas import UpdatedUserResponse
from api.users.schemas import UpdateUserRequest
from api.users.schemas import UserCreate
from db.models import User
from db.session import get_session
from utils.decorators import only_superadmin

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
    target_user = await fetch_user_or_raise(user_id, current_user, session)
    if (
        target_user == current_user
        and current_user.is_superadmin
    ):
        raise HTTPException(
            status_code=406, detail="Superadmin cannot be deleted via API."
        )

    if not await check_user_permissions(
        target_user=target_user, current_user=current_user
    ):
        raise HTTPException(status_code=403, detail="Forbidden.")

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
    target_user = await fetch_user_or_raise(user_id, current_user, session)
    if not await check_user_permissions(
        target_user=target_user, current_user=current_user
    ):
        raise HTTPException(status_code=403, detail="Forbidden.")

    activated_user_id = await activate_user_action(user_id, session)
    return ActivateUserResponse(activated_user_id=activated_user_id)


@user_router.get("/", response_model=ShowUser)
async def get_user_by_id(
    user_id: UUID,
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
    session: AsyncSession = Depends(get_session),
) -> ShowUser:
    target_user = await fetch_user_or_raise(user_id, current_user, session)
    if not await check_user_permissions(
        target_user=target_user, current_user=current_user
    ):
        raise HTTPException(status_code=403, detail="Forbidden.")

    return ShowUser(
        user_id=target_user.user_id,
        name=target_user.name,
        surname=target_user.surname,
        email=target_user.email,
        is_active=target_user.is_active,
    )


@user_router.patch("/", response_model=UpdatedUserResponse)
async def update_user_by_id(
    user_id: UUID,
    body: UpdateUserRequest,
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
    session: AsyncSession = Depends(get_session),
) -> UpdatedUserResponse:
    target_user = await fetch_user_or_raise(user_id, current_user, session)
    if not await check_user_permissions(
        target_user=target_user, current_user=current_user
    ):
        raise HTTPException(status_code=403, detail="Forbidden.")

    try:
        updated_user_id = await process_user_update_request_action(user_id, body, session)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UpdatedUserResponse(updated_user_id=updated_user_id)





@user_router.patch("/admin_privilege", response_model=UpdatedUserResponse)
@only_superadmin
async def grant_admin_privilege(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
):
    try:
        updated_user_id = await grant_admin_privilege_action(
            user_id=user_id,
            current_user=current_user,
            session=session,
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UpdatedUserResponse(updated_user_id=updated_user_id)


@user_router.delete("/admin_privilege", response_model=UpdatedUserResponse)
@only_superadmin
async def revoke_admin_privilege(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(AuthService.get_current_user_from_access_token),
):
    try:
        updated_user_id = await revoke_admin_privilege_action(
            user_id=user_id,
            current_user=current_user,
            session=session,
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UpdatedUserResponse(updated_user_id=updated_user_id)