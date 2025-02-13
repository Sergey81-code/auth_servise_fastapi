from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select

from db.models import User
from scripts.delete_superadmin import delete_superadmin
from utils.hashing import Hasher
from utils.roles import PortalRole


async def test_delete_superadmin(async_session_test, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "email": "test@example.com",
        "password": "StrongPass1!",
        "name": "Super",
        "surname": "Admin",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }

    await create_user_in_database(user_data)

    async with async_session_test() as session:
        await delete_superadmin(user_data["email"], session)

        result = await session.execute(select(User))

        users = result.scalars().all()

    assert len(users) == 0


async def test_delete_superadmin_email_not_found(
    async_session_test, create_user_in_database, get_user_from_database
):
    user_data = {
        "user_id": uuid4(),
        "email": "test@example.com",
        "password": "StrongPass1!",
        "name": "Super",
        "surname": "Admin",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }

    await create_user_in_database(user_data)

    email_not_exists = "nonexistent@example.com"

    async with async_session_test() as session:
        with patch("builtins.print") as mock_print:
            await delete_superadmin(email_not_exists, session)
            mock_print.assert_any_call("Error: A user with this email does not exist.")

    resp_data = (await get_user_from_database(user_data["user_id"]))[0]

    assert resp_data["user_id"] == user_data["user_id"]
    assert resp_data["name"] == user_data["name"]
    assert resp_data["surname"] == user_data["surname"]
    assert resp_data["email"] == user_data["email"]
    assert resp_data["is_active"] is user_data["is_active"]
    assert Hasher.verify_password(user_data["password"], resp_data["hashed_password"])
    assert resp_data["roles"] == user_data["roles"]
