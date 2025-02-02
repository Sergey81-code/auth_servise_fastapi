from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.users.models import UserCreate
from db.dals import UserDAL
from db.models import User
from utils.hashing import Hasher


async def _create_new_user(body: UserCreate, db: AsyncSession) -> User:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            return await user_dal.create_user(
                name=body.name,
                surname=body.surname,
                email=body.email,
                hashed_password=Hasher.get_password_hash(body.password),
            )


async def _delete_user(user_id: UUID, db: AsyncSession) -> UUID | None:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            deleted_user_id = await user_dal.delete_user(
                user_id=user_id,
            )
            return deleted_user_id


async def _activate_user(user_id: UUID, db: AsyncSession) -> UUID | None:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            activated_user_id = await user_dal.activate_user(
                user_id=user_id,
            )
            return activated_user_id
        

async def _update_user(
    user_id: UUID, updated_user_params: dict, db: AsyncSession
) -> UUID | None:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            del updated_user_params['old_password']
            if updated_user_params['new_password']:
                updated_user_params['hashed_password'] = Hasher.get_password_hash(updated_user_params['new_password'])
                del updated_user_params['new_password']
            updated_user_id = await user_dal.update_user(
                user_id=user_id, **updated_user_params
            )
            return updated_user_id


async def _get_user_by_id(user_id: UUID, db: AsyncSession) -> User | None:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            return await user_dal.get_user_by_id(user_id)