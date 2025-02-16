import asyncio
from uuid import uuid4

import pytest

from tests.conftest import create_test_auth_headers_for_user
from tests.conftest import USER_URL
from utils.hashing import Hasher
from utils.roles import PortalRole


async def test_update_user(client, create_user_in_database, get_user_from_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    user_data_updated = {
        "old_password": user_data["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
        "new_password": "Abcd12!@1",
    }
    await create_user_in_database(user_data)
    resp = client.patch(
        f"{USER_URL}?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
        json=user_data_updated,
    )
    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["updated_user_id"] == str(user_data["user_id"])
    users_from_db = await get_user_from_database(user_data["user_id"])
    assert len(users_from_db) == 1
    user_from_db = dict(users_from_db[0])
    assert user_from_db["user_id"] == user_data["user_id"]
    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert Hasher.verify_password(
        user_data_updated["new_password"], user_from_db["hashed_password"]
    )
    assert user_from_db["is_active"] is user_data["is_active"]


async def test_update_only_one_user(
    client, create_user_in_database, get_user_from_database
):
    user1 = {
        "user_id": uuid4(),
        "name": "name1",
        "email": "email1@gmail.ru",
        "surname": "surname1",
        "password": "Abcd12!@",
        "is_active": True,
    }
    user2 = {
        "user_id": uuid4(),
        "name": "name2",
        "email": "email2@gmail.ru",
        "surname": "surname2",
        "password": "Abcd12!@",
        "is_active": True,
    }
    user3 = {
        "user_id": uuid4(),
        "name": "name3",
        "email": "email3@gmail.ru",
        "surname": "surname3",
        "password": "Abcd12!@",
        "is_active": True,
    }

    user1_update_data = {
        "old_password": user1["password"],
        "name": "name",
        "surname": "surname",
        "email": "email@mail.ru",
        "new_password": "AAbcd12!@",
    }

    created_request = [
        create_user_in_database(user_data) for user_data in [user1, user2, user3]
    ]

    await asyncio.gather(*created_request)

    resp = client.patch(
        f"{USER_URL}?user_id={user1['user_id']}",
        headers=await create_test_auth_headers_for_user(user1["email"]),
        json=user1_update_data,
    )
    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["updated_user_id"] == str(user1["user_id"])

    user1_from_db = await get_user_from_database(user1["user_id"])
    user1_from_db = dict(user1_from_db[0])
    user2_from_db = await get_user_from_database(user2["user_id"])
    user2_from_db = dict(user2_from_db[0])
    user3_from_db = await get_user_from_database(user3["user_id"])
    user3_from_db = dict(user3_from_db[0])

    assert user1_from_db["user_id"] == user1["user_id"]
    assert user1_from_db["name"] == user1_update_data["name"]
    assert user1_from_db["surname"] == user1_update_data["surname"]
    assert user1_from_db["email"] == user1_update_data["email"]
    assert Hasher.verify_password(
        user1_update_data["new_password"], user1_from_db["hashed_password"]
    )
    assert user1_from_db["is_active"] is user1["is_active"]

    assert user2_from_db["user_id"] == user2["user_id"]
    assert user2_from_db["name"] == user2["name"]
    assert user2_from_db["surname"] == user2["surname"]
    assert user2_from_db["email"] == user2["email"]
    assert Hasher.verify_password(user2["password"], user2_from_db["hashed_password"])
    assert user2_from_db["is_active"] is user2["is_active"]

    assert user3_from_db["user_id"] == user3["user_id"]
    assert user3_from_db["name"] == user3["name"]
    assert user3_from_db["surname"] == user3["surname"]
    assert user3_from_db["email"] == user3["email"]
    assert Hasher.verify_password(user3["password"], user3_from_db["hashed_password"])
    assert user3_from_db["is_active"] is user3["is_active"]


@pytest.mark.parametrize(
    "user_data_updated, expected_status_code, expected_detail",
    [
        (
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "old_password"],
                        "msg": "Field required",
                        "input": {},
                    }
                ]
            },
        ),
        (
            {"old_password": "Abcd12!@", "name": "123"},
            422,
            {"detail": "Name should contains only letters"},
        ),
        (
            {"old_password": "Abcd12!@", "surname": "123"},
            422,
            {"detail": "Surname should contains only letters"},
        ),
        (
            {"old_password": "Abcd12!@", "email": "123"},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "123",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
        (
            {"old_password": "Abcd12!@", "email": ""},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
        (
            {"old_password": "Abcd12!@", "name": ""},
            422,
            {"detail": "Name should contains only letters"},
        ),
        (
            {"old_password": "Abcd12!@", "surname": ""},
            422,
            {"detail": "Surname should contains only letters"},
        ),
        (
            {"old_password": "Abcd12!@", "new_password": ""},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345678"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345678aa"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345678AA"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345678Aa"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345678A!@"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"old_password": "Abcd12!@", "new_password": "12345678a!@"},
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {"name": "Sergey", "email": "joker@mail.ru"},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "old_password"],
                        "msg": "Field required",
                        "input": {"name": "Sergey", "email": "joker@mail.ru"},
                    }
                ]
            },
        ),
    ],
)
async def test_update_user_validation_error(
    client,
    create_user_in_database,
    user_data_updated,
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
    resp = client.patch(
        f"{USER_URL}?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
        json=user_data_updated,
    )
    assert resp.status_code == expected_status_code
    resp_data = resp.json()
    assert resp_data == expected_detail


async def test_update_user_id_validation_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    user_data_updated = {
        "old_password": user_data["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    resp = client.patch(
        f"{USER_URL}?user_id=123",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
        json=user_data_updated,
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


async def test_update_user_not_found_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER, PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data)
    user_data_updated = {
        "old_password": user_data["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    user_id_for_finding = uuid4()
    resp = client.patch(
        f"{USER_URL}?user_id={user_id_for_finding}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
        json=user_data_updated,
    )
    assert resp.status_code == 404
    data_from_response = resp.json()
    assert data_from_response == {
        "detail": f"User with id {user_id_for_finding} not found."
    }


async def test_update_user_dublicate_email_error(client, create_user_in_database):
    user_data1 = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    user_data2 = {
        "user_id": uuid4(),
        "name": "Nikolaii",
        "surname": "Sviridovv",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data1)
    await create_user_in_database(user_data2)
    user_data_dublicate_email = {
        "old_password": user_data1["password"],
        "email": user_data2["email"],
    }
    resp = client.patch(
        f"{USER_URL}?user_id={user_data1['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data1["email"]),
        json=user_data_dublicate_email,
    )
    assert resp.status_code == 503
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in resp.json()["detail"]
    )


async def test_get_user_bad_cred(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    user_data_updated = {
        "old_password": user_data["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
        "new_password": "Abcd12!@1",
    }
    await create_user_in_database(user_data)
    resp = client.patch(
        f"{USER_URL}?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"] + "a"),
        json=user_data_updated,
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
    user_data_updated = {
        "old_password": user_data["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
        "new_password": "Abcd12!@1",
    }
    await create_user_in_database(user_data)
    bad_auth_headers = await create_test_auth_headers_for_user(user_data["email"])
    bad_auth_headers["Authorization"] += "a"
    resp = client.patch(
        f"{USER_URL}?user_id={user_data['user_id']}",
        headers=bad_auth_headers,
        json=user_data_updated,
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
    user_data_updated = {
        "old_password": user_data["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
        "new_password": "Abcd12!@1",
    }
    await create_user_in_database(user_data)
    resp = client.patch(
        f"{USER_URL}?user_id={user_data['user_id']}",
        json=user_data_updated,
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    "user_role_list",
    [
        [PortalRole.ROLE_PORTAL_USER, PortalRole.ROLE_PORTAL_ADMIN],
        [PortalRole.ROLE_PORTAL_USER, PortalRole.ROLE_PORTAL_SUPERADMIN],
        [PortalRole.ROLE_PORTAL_ADMIN, PortalRole.ROLE_PORTAL_SUPERADMIN],
    ],
)
async def test_update_user_by_privilage_roles(
    client, create_user_in_database, get_user_from_database, user_role_list
):
    user_data_for_updating = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_data_updated = {
        "old_password": user_data_for_updating["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
        "new_password": "Abcd12!@1",
    }
    user_who_update = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": user_role_list,
    }

    await create_user_in_database(user_data_for_updating)
    await create_user_in_database(user_who_update)
    resp = client.patch(
        f"{USER_URL}?user_id={user_data_for_updating['user_id']}",
        json=user_data_updated,
        headers=await create_test_auth_headers_for_user(user_who_update["email"]),
    )
    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["updated_user_id"] == str(user_data_for_updating["user_id"])
    users_from_db = await get_user_from_database(user_data_for_updating["user_id"])
    assert len(users_from_db) == 1
    user_from_db = dict(users_from_db[0])
    assert user_from_db["user_id"] == user_data_for_updating["user_id"]
    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert Hasher.verify_password(
        user_data_updated["new_password"], user_from_db["hashed_password"]
    )
    assert user_from_db["is_active"] is user_data_for_updating["is_active"]


@pytest.mark.parametrize(
    "user_data_for_updating, user_who_update",
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
async def test_update_another_user_error(
    client,
    create_user_in_database,
    user_data_for_updating,
    user_who_update,
):
    user_data_updated = {
        "old_password": user_data_for_updating["password"],
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
        "new_password": "Abcd12!@1",
    }
    await create_user_in_database(user_data_for_updating)
    await create_user_in_database(user_who_update)
    reps = client.patch(
        f"{USER_URL}?user_id={user_data_for_updating['user_id']}",
        json=user_data_updated,
        headers=await create_test_auth_headers_for_user(user_who_update["email"]),
    )
    assert reps.status_code == 403
