from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from db.models import User
from scripts.create_superadmin import create_superadmin
from scripts.create_superadmin import prompt_for_superadmin_credentials
from utils.hashing import Hasher
from utils.roles import PortalRole


@patch(
    "builtins.input", side_effect=["test@example.com", "StrongPass1!", "Super", "Admin"]
)
async def test_prompt_for_superadmin_credentials(mock_input):
    with patch(
        "scripts.create_superadmin.create_superadmin", new_callable=AsyncMock
    ) as mock_create_superadmin:
        await prompt_for_superadmin_credentials()
        mock_create_superadmin.assert_called_once_with(
            "test@example.com", "StrongPass1!", "Super", "Admin", ANY
        )


async def test_prompt_for_superadmin_credentials_invalid_email():
    with patch(
        "builtins.input",
        side_effect=[
            "invalid_email",
            "test@example.com",
            "StrongPass1!",
            "Super",
            "Admin",
        ],
    ), patch(
        "scripts.create_superadmin.create_superadmin", new_callable=AsyncMock
    ) as mock_create_superadmin:
        await prompt_for_superadmin_credentials()
        mock_create_superadmin.assert_called_once_with(
            "test@example.com", "StrongPass1!", "Super", "Admin", ANY
        )


async def test_prompt_for_superadmin_credentials_invalid_password():
    with patch(
        "builtins.input",
        side_effect=[
            "test@example.com",
            "invalid-password",
            "StrongPass1!",
            "Super",
            "Admin",
        ],
    ), patch(
        "scripts.create_superadmin.create_superadmin", new_callable=AsyncMock
    ) as mock_create_superadmin:
        await prompt_for_superadmin_credentials()
        mock_create_superadmin.assert_called_once_with(
            "test@example.com", "StrongPass1!", "Super", "Admin", ANY
        )


async def test_prompt_for_superadmin_credentials_exit():
    with patch("builtins.input", side_effect=["exit"]), patch(
        "sys.exit", side_effect=SystemExit(0)
    ) as mock_exit:
        with pytest.raises(SystemExit):
            await prompt_for_superadmin_credentials()
        mock_exit.assert_called_once_with(0)


async def test_create_superadmin(async_session_test):
    user_data = {
        "email": "test@example.com",
        "password": "StrongPass1!",
        "name": "Super",
        "surname": "Admin",
    }

    async with async_session_test() as session:
        await create_superadmin(**user_data, session=session)

        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )

        user = result.scalar_one_or_none()

        assert user is not None
        assert user.name == user_data["name"]
        assert user.surname == user_data["surname"]
        assert user.email == user_data["email"]
        assert user.is_active == True
        assert Hasher.verify_password(user_data["password"], user.hashed_password)
        assert PortalRole.ROLE_PORTAL_SUPERADMIN in user.roles


async def test_create_superadmin_already_exists(
    async_session_test, create_user_in_database
):
    first_user_data = {
        "user_id": uuid4(),
        "email": "test@example.com",
        "password": "StrongPass1!",
        "name": "Super",
        "surname": "Admin",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }

    second_user_data = {
        "email": "test@example.com",
        "password": "StrongPass111!",
        "name": "Super1",
        "surname": "Admin1",
    }

    await create_user_in_database(first_user_data)

    async with async_session_test() as session:
        await create_superadmin(**second_user_data, session=session)

        result = await session.execute(
            select(User).where(User.email == first_user_data["email"])
        )

        users = result.scalars().all()  # Получаем все результаты как список

        assert len(users) == 1  # Теперь можем проверить длину списка
        user = users[0]

        assert user is not None
        assert user.name == first_user_data["name"]
        assert user.surname == first_user_data["surname"]
        assert user.email == first_user_data["email"]
        assert user.is_active is True
        assert Hasher.verify_password(first_user_data["password"], user.hashed_password)
        assert PortalRole.ROLE_PORTAL_SUPERADMIN in user.roles
