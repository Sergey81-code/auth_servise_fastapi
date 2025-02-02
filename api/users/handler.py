from logging import getLogger
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.users.actions import _activate_user
from api.users.actions import _create_new_user
from api.users.actions import _delete_user
from api.users.actions import _get_user_by_id
from api.users.actions import _update_user
from api.users.models import ActivateUserResponse
from api.users.models import DeleteUserResponse
from api.users.models import ShowUser
from api.users.models import UpdatedUserResponse
from api.users.models import UpdateUserRequest
from api.users.models import UserCreate
from db.session import get_db
from utils.hashing import Hasher

logger = getLogger(__name__)

user_router = APIRouter()


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    try:
        user = await _create_new_user(body, db)
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
    user_id: UUID, db: AsyncSession = Depends(get_db)
) -> DeleteUserResponse:
    deleted_user_id = await _delete_user(user_id, db)
    if deleted_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return DeleteUserResponse(deleted_user_id=deleted_user_id)


@user_router.post("/activate", response_model=ActivateUserResponse)
async def activate_user(
    user_id: UUID, db: AsyncSession = Depends(get_db)
) -> ActivateUserResponse:
    activated_user_id = await _activate_user(user_id, db)
    if activated_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return ActivateUserResponse(activated_user_id=activated_user_id)


@user_router.get("/", response_model=ShowUser)
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)) -> ShowUser:
    user = await _get_user_by_id(user_id, db)
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
    user_id: UUID, body: UpdateUserRequest, db: AsyncSession = Depends(get_db)
) -> UpdatedUserResponse:
    updated_user_params = body.model_dump(exclude_none=True)
    if updated_user_params == {}:
        raise HTTPException(
            status_code=422,
            detail="At least one parameter for user update info should be proveded",
        )
    user = await _get_user_by_id(user_id, db)

    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    if not Hasher.verify_password(
        updated_user_params["old_password"], user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    try:
        updated_user_id = await _update_user(
            user_id, updated_user_params=updated_user_params, db=db
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UpdatedUserResponse(updated_user_id=updated_user_id)
