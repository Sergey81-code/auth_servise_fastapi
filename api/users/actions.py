from uuid import UUID

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from api.users.schemas import UpdateUserRequest
from api.users.schemas import UserCreate
from db.dals import UserDAL
from db.models import User
from utils.hashing import Hasher
from utils.roles import PortalRole


async def create_new_user_action(body: UserCreate, session: AsyncSession) -> User:
    async with session.begin():
        return await UserDAL(session).create_user(
            name=body.name,
            surname=body.surname,
            email=body.email,
            hashed_password=Hasher.get_password_hash(body.password),
            roles=[PortalRole.ROLE_PORTAL_USER],
        )


async def delete_user_action(user_id: UUID, session: AsyncSession) -> UUID | None:
    async with session.begin():
        return await UserDAL(session).delete_user(
            user_id=user_id,
        )


async def activate_user_action(user_id: UUID, session: AsyncSession) -> UUID | None:
    async with session.begin():
        return await UserDAL(session).activate_user(
            user_id=user_id,
        )


async def process_user_update_request_action(
    user_id: UUID, updated_user_params: UpdateUserRequest, session: AsyncSession
) -> UUID | None:
    updated_params = updated_user_params.model_dump(exclude_none=True)
    user = await get_user_by_id_action(user_id, session)

    old_password = updated_params.pop("old_password", None)
    if not old_password or not Hasher.verify_password(
        old_password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    if not updated_params:
        raise HTTPException(
            status_code=422,
            detail="At least one parameter for user update info should be proveded",
        )

    if new_password := updated_params.pop("new_password", None):
        updated_params["hashed_password"] = Hasher.get_password_hash(new_password)

    return await update_user_action(user_id, updated_params, session)


async def update_user_action(
    user_id: UUID, updated_user_params: dict, session: AsyncSession
) -> UUID | None:
    async with session.begin():
        return await UserDAL(session).update_user(
            user_id=user_id, **updated_user_params
        )


async def get_user_by_id_action(user_id: UUID, session: AsyncSession) -> User | None:
    async with session.begin():
        return await UserDAL(session).get_user_by_id(user_id)


async def get_user_by_email_action(email: str, session: AsyncSession) -> User | None:
    async with session.begin():
        return await UserDAL(session).get_user_by_email(email=email)


async def fetch_user_or_raise(
    user_id: UUID, current_user: User, session: AsyncSession
) -> User:
    target_user = await get_user_by_id_action(user_id, session)
    if target_user is None:
        if current_user.is_admin or current_user.is_superadmin:
            raise HTTPException(
                status_code=404, detail=f"User with id {user_id} not found."
            )
        raise HTTPException(status_code=403, detail="Forbidden")
    return target_user


async def check_user_permissions(target_user: User, current_user: User) -> bool:
    if target_user == current_user:
        return True
    if target_user.is_superadmin:
        return False
    if current_user.is_superadmin:
        return True
    if current_user.is_admin and not target_user.is_admin:
        return True
    return False


async def grant_admin_privilege_action(
    user_id: UUID, current_user: User, session: AsyncSession
) -> UUID | None:
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400, detail="Cannot manage privileges of itself."
        )
    user_for_promotion = await fetch_user_or_raise(user_id, current_user, session)
    if user_for_promotion.is_admin or user_for_promotion.is_superadmin:
        raise HTTPException(
            status_code=409,
            detail=f"User with email {user_for_promotion.email} already promoted to admin / superadmin",
        )
    return await update_user_action(
        user_id=user_id,
        updated_user_params={"roles": user_for_promotion.extend_roles_with_admin()},
        session=session,
    )


async def revoke_admin_privilege_action(
    user_id: UUID, current_user: User, session: AsyncSession
) -> UUID | None:
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400, detail="Cannot manage privileges of itself."
        )
    user_for_promotion = await fetch_user_or_raise(user_id, current_user, session)
    if not user_for_promotion.is_admin:
        raise HTTPException(
            status_code=409,
            detail=f"User with email {user_for_promotion.email} has no admin privileges",
        )
    return await update_user_action(
        user_id=user_id,
        updated_user_params={"roles": user_for_promotion.exclude_admin_role()},
        session=session,
    )
