from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.users.models import UpdateUserRequest, UserCreate
from db.dals import UserDAL
from db.models import User
from utils.hashing import Hasher
from utils.roles import PortalRole


async def create_new_user_action(body: UserCreate, session: AsyncSession) -> User:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.create_user(
            name=body.name,
            surname=body.surname,
            email=body.email,
            hashed_password=Hasher.get_password_hash(body.password),
            roles=[PortalRole.ROLE_PORTAL_USER, ]
        )


async def delete_user_action(user_id: UUID, session: AsyncSession) -> UUID | None:
    async with session.begin():
        user_dal = UserDAL(session)
        deleted_user_id = await user_dal.delete_user(
            user_id=user_id,
        )
        return deleted_user_id


async def activate_user_action(user_id: UUID, session: AsyncSession) -> UUID | None:
    async with session.begin():
        user_dal = UserDAL(session)
        activated_user_id = await user_dal.activate_user(
            user_id=user_id,
        )
        return activated_user_id
    

async def _validate_updated_user_params(user_id: UUID, updated_user_params: dict, session: AsyncSession) -> dict:
    user = await get_user_by_id_action(user_id, session)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    
    if not Hasher.verify_password(
        updated_user_params["old_password"], user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    del updated_user_params["old_password"]
    
    if updated_user_params == {}:
        raise HTTPException(
            status_code=422,
            detail="At least one parameter for user update info should be proveded",
        )
    
    return updated_user_params
    


async def update_user_action(
    user_id: UUID, updated_user_params: UpdateUserRequest, session: AsyncSession
) -> UUID | None:
    updated_user_params = updated_user_params.model_dump(exclude_none=True)
    validated_updated_user_params = await _validate_updated_user_params(user_id, updated_user_params, session)

    if "new_password" in validated_updated_user_params.keys():
        validated_updated_user_params["hashed_password"] = Hasher.get_password_hash(
            validated_updated_user_params["new_password"]
        )
        del validated_updated_user_params["new_password"]
            
    async with session.begin():
        user_dal = UserDAL(session)
        updated_user_id = await user_dal.update_user(
            user_id=user_id, **validated_updated_user_params
        )
        return updated_user_id


async def get_user_by_id_action(user_id: UUID, session: AsyncSession) -> User | None:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.get_user_by_id(user_id)


async def get_user_by_email_action(email: str, session: AsyncSession) -> User | None:
    async with session.begin():
        user_dal = UserDAL(session)
        user = await user_dal.get_user_by_email(email=email)
        return user
