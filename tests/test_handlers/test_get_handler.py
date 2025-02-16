from uuid import uuid4

import pytest

from tests.conftest import create_test_auth_headers_for_user
from tests.conftest import USER_URL
from utils.roles import PortalRole


async def test_get_user(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.get(
        f"{USER_URL}?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 200
    user_from_response = resp.json()
    assert user_from_response["user_id"] == str(user_data["user_id"])
    assert user_from_response["name"] == user_data["name"]
    assert user_from_response["surname"] == user_data["surname"]
    assert user_from_response["email"] == user_data["email"]
    assert user_from_response["is_active"] is user_data["is_active"]


async def test_get_user_id_validation_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.get(
        f"{USER_URL}?user_id=123",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 422
    data_from_response = resp.json()
    assert data_from_response == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "user_id"],
                "msg": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3",
                "input": "123",
                "ctx": {
                    "error": "invalid length: expected length 32 for simple format, found 3"
                },
            }
        ]
    }


async def test_get_user_not_found_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER, PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    user_id_for_finding = uuid4()
    await create_user_in_database(user_data)
    resp = client.get(
        f"{USER_URL}?user_id={user_id_for_finding}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 404
    data_from_response = resp.json()
    assert data_from_response == {
        "detail": f"User with id {user_id_for_finding} not found."
    }


async def test_get_user_bad_cred(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.get(
        f"{USER_URL}?user_id={user_data["user_id"]}",
        headers=await create_test_auth_headers_for_user(user_data["email"] + "a"),
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Could not validate credentials"}


async def test_get_user_unauth(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    bad_auth_headers = await create_test_auth_headers_for_user(user_data["email"])
    bad_auth_headers["Authorization"] += "a"
    resp = client.get(
        f"{USER_URL}?user_id={user_data["user_id"]}",
        headers=bad_auth_headers,
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Could not validate credentials"}


async def test_get_user_no_jwt(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.get(
        f"{USER_URL}?user_id={user_data["user_id"]}",
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    "user_role_list",
    [
        [PortalRole.ROLE_PORTAL_USER, PortalRole.ROLE_PORTAL_ADMIN],
        [PortalRole.ROLE_PORTAL_ADMIN, PortalRole.ROLE_PORTAL_SUPERADMIN],
        [PortalRole.ROLE_PORTAL_USER, PortalRole.ROLE_PORTAL_SUPERADMIN],
    ],
)
async def test_get_user_by_privilage_roles(
    client, create_user_in_database, user_role_list
):
    user_data_for_getting = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_who_get = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": user_role_list,
    }
    await create_user_in_database(user_data_for_getting)
    await create_user_in_database(user_who_get)
    resp = client.get(
        f"{USER_URL}?user_id={user_data_for_getting['user_id']}",
        headers=await create_test_auth_headers_for_user(user_who_get["email"]),
    )
    assert resp.status_code == 200
    user_from_response = resp.json()
    assert user_from_response["user_id"] == str(user_data_for_getting["user_id"])
    assert user_from_response["name"] == user_data_for_getting["name"]
    assert user_from_response["surname"] == user_data_for_getting["surname"]
    assert user_from_response["email"] == user_data_for_getting["email"]
    assert user_from_response["is_active"] is user_data_for_getting["is_active"]


@pytest.mark.parametrize(
    "user_for_getting, user_who_get",
    [
        (
            {
                "user_id": uuid4(),
                "name": "Nikolai",
                "surname": "Sviridov",
                "email": "lol@kek.com",
                "is_active": True,
                "password": "SampleHashedPass",
                "roles": [PortalRole.ROLE_PORTAL_USER],
            },
            {
                "user_id": uuid4(),
                "name": "Admin",
                "surname": "Adminov",
                "email": "admin@kek.com",
                "is_active": True,
                "password": "SampleHashedPass",
                "roles": [PortalRole.ROLE_PORTAL_USER],
            },
        ),
        (
            {
                "user_id": uuid4(),
                "name": "Nikolai",
                "surname": "Sviridov",
                "email": "lol@kek.com",
                "is_active": True,
                "password": "SampleHashedPass",
                "roles": [
                    PortalRole.ROLE_PORTAL_USER,
                    PortalRole.ROLE_PORTAL_SUPERADMIN,
                ],
            },
            {
                "user_id": uuid4(),
                "name": "Admin",
                "surname": "Adminov",
                "email": "admin@kek.com",
                "is_active": True,
                "password": "SampleHashedPass",
                "roles": [
                    PortalRole.ROLE_PORTAL_USER,
                    PortalRole.ROLE_PORTAL_ADMIN,
                ],
            },
        ),
        (
            {
                "user_id": uuid4(),
                "name": "Nikolai",
                "surname": "Sviridov",
                "email": "lol@kek.com",
                "is_active": True,
                "password": "SampleHashedPass",
                "roles": [
                    PortalRole.ROLE_PORTAL_USER,
                    PortalRole.ROLE_PORTAL_ADMIN,
                ],
            },
            {
                "user_id": uuid4(),
                "name": "Admin",
                "surname": "Adminov",
                "email": "admin@kek.com",
                "is_active": True,
                "password": "SampleHashedPass",
                "roles": [
                    PortalRole.ROLE_PORTAL_USER,
                    PortalRole.ROLE_PORTAL_ADMIN,
                ],
            },
        ),
    ],
)
async def test_get_another_user_error(
    client,
    create_user_in_database,
    user_for_getting,
    user_who_get,
):
    await create_user_in_database(user_for_getting)
    await create_user_in_database(user_who_get)
    reps = client.get(
        f"{USER_URL}?user_id={user_for_getting['user_id']}",
        headers=await create_test_auth_headers_for_user(user_who_get["email"]),
    )
    assert reps.status_code == 403
