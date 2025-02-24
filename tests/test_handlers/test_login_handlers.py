from uuid import uuid4

import pytest

from api.core.config import get_settings
from tests.conftest import assert_token_lifetime
from tests.conftest import create_test_jwt_token_for_user
from tests.conftest import get_test_data_from_jwt_token
from tests.conftest import LOGIN_URL
from utils.roles import PortalRole

settings = get_settings()


async def test_user_login(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    await create_user_in_database(user_data)
    user_data_for_login = {
        "username": user_data["email"],
        "password": user_data["password"],
    }
    resp = client.post(f"{LOGIN_URL}", data=user_data_for_login)
    assert resp.status_code == 200

    resp_data = resp.json()
    assert resp_data["token_type"] == "bearer"

    resp_cookies_data = dict(resp.cookies)
    resp_data_from_access = await get_test_data_from_jwt_token(
        resp_data["access_token"], "access"
    )
    resp_data_from_refresh = await get_test_data_from_jwt_token(
        resp_cookies_data["refresh_token"], "refresh"
    )

    assert resp_data_from_access["sub"] == user_data["email"]
    assert resp_data_from_access["user_id"] == str(user_data["user_id"])
    assert resp_data_from_access["roles"] == user_data["roles"]
    assert resp_data_from_refresh["sub"] == user_data["email"]


    assert await assert_token_lifetime(
        resp_data_from_access, settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    assert await assert_token_lifetime(
        resp_data_from_refresh, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
    )


async def test_create_access_token_by_refresh_token(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    await create_user_in_database(user_data)
    refresh_token = await create_test_jwt_token_for_user(user_data["email"], "refresh")
    resp = client.post(f"{LOGIN_URL}token", cookies={"refresh_token": refresh_token})
    assert resp.status_code == 200

    resp_data = resp.json()
    assert resp_data["token_type"] == "bearer"

    resp_data_from_access = await get_test_data_from_jwt_token(
        resp_data["access_token"], "access"
    )
    assert resp_data_from_access["sub"] == user_data["email"]
    assert resp_data_from_access["user_id"] == str(user_data["user_id"])
    assert resp_data_from_access["roles"] == user_data["roles"]
    assert await assert_token_lifetime(
        resp_data_from_access, settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@pytest.mark.parametrize(
    "login_data, expected_status_code, expected_detail",
    [
        (
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "username"],
                        "msg": "Field required",
                        "input": None,
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": None,
                    },
                ],
            },
        ),
        (
            {"username": "", "password": ""},
            401,
            {"detail": "Incorrect username or password"},
        ),
        (
            {"username": "lol@kek.com", "password": ""},
            401,
            {"detail": "Incorrect username or password"},
        ),
        (
            {"username": "", "password": "Abcd12!@"},
            401,
            {"detail": "Incorrect username or password"},
        ),
        (
            {"username": "lol1@kek.com", "password": "Abcd12!@"},
            401,
            {"detail": "Incorrect username or password"},
        ),
        (
            {"username": "lol@kek.com", "password": "Abcd12!@1"},
            401,
            {"detail": "Incorrect username or password"},
        ),
        (
            {"email": "lol@kek.com", "password": "Abcd12!@"},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "username"],
                        "msg": "Field required",
                        "input": None,
                    },
                ],
            },
        ),
        (
            {"username": "lol@kek.com", "hashed_password": "Abcd12!@"},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": None,
                    }
                ]
            },
        ),
    ],
)
async def test_user_login_validation_error(
    client, create_user_in_database, login_data, expected_status_code, expected_detail
):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.post(f"{LOGIN_URL}", data=login_data)

    assert resp.status_code == expected_status_code
    assert resp.json() == expected_detail


@pytest.mark.parametrize(
    "refresh_token, expected_status_code, expected_detail",
    [
        (
            "",
            401,
            {"detail": "Could not validate credentials"},
        ),
        (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzZWJhbm55QG1haWwucnUiLCJvdGhlcl9jdXN0b21fZGF0YSI6WzEsMiwzLDRdLCJleHAiOjE3Mzk2OTYxMjN9.N34lqvVeH0wOZmZnu1iz83QQ-H9KbPQ66GWUzmtdQ6a",
            401,
            {"detail": "Could not validate credentials"},
        ),
    ],
)
async def test_create_access_token_by_refresh_token_error(
    client,
    create_user_in_database,
    refresh_token,
    expected_status_code,
    expected_detail,
):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.post(f"{LOGIN_URL}token", cookies={"refresh_token": refresh_token})

    assert resp.status_code == expected_status_code
    assert resp.json() == expected_detail
