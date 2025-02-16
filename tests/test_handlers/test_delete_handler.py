from uuid import uuid4

import pytest

from tests.conftest import USER_URL, create_test_auth_headers_for_user
from utils.roles import PortalRole


async def test_delete_user(client, create_user_in_database, get_user_from_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.delete(
        f"{USER_URL}?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 200
    assert resp.json() == {"deleted_user_id": str(user_data["user_id"])}
    users_from_db = await get_user_from_database(user_data["user_id"])
    user_from_db = dict(users_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is False
    assert user_from_db["user_id"] == user_data["user_id"]


async def test_delete_user_id_validation_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.delete(
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


async def test_delete_user_not_found_error(client, create_user_in_database):
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
    user_id_not_exist = uuid4()
    resp = client.delete(
        f"{USER_URL}?user_id={user_id_not_exist}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 404
    data_from_response = resp.json()
    assert data_from_response == {
        "detail": f"User with id {user_id_not_exist} not found."
    }


async def test_delete_user_bad_cred(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.delete(
        f"{USER_URL}?user_id={user_data["user_id"]}",
        headers=await create_test_auth_headers_for_user(user_data["email"] + "a"),
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Could not validate credentials"}


async def test_delete_user_unauth(client, create_user_in_database):
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
    resp = client.delete(
        f"{USER_URL}?user_id={user_data["user_id"]}",
        headers=bad_auth_headers,
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Could not validate credentials"}


async def test_delete_user_no_jwt(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    await create_user_in_database(user_data)
    resp = client.delete(
        f"{USER_URL}?user_id={user_data["user_id"]}",
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
async def test_delete_user_by_privilage_roles(
    client, create_user_in_database, get_user_from_database, user_role_list
):
    user_data_for_deletion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_who_delete = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": user_role_list,
    }
    await create_user_in_database(user_data_for_deletion)
    await create_user_in_database(user_who_delete)
    resp = client.delete(
        f"{USER_URL}?user_id={user_data_for_deletion['user_id']}",
        headers=await create_test_auth_headers_for_user(user_who_delete["email"]),
    )
    assert resp.status_code == 200
    assert resp.json() == {"deleted_user_id": str(user_data_for_deletion["user_id"])}
    users_from_db = await get_user_from_database(user_data_for_deletion["user_id"])
    user_form_db = dict(users_from_db[0])
    assert user_form_db["name"] == user_data_for_deletion["name"]
    assert user_form_db["surname"] == user_data_for_deletion["surname"]
    assert user_form_db["email"] == user_data_for_deletion["email"]
    assert user_form_db["is_active"] is False
    assert user_form_db["user_id"] == user_data_for_deletion["user_id"]


@pytest.mark.parametrize(
    "user_for_deletion, user_who_delete",
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
async def test_delete_another_user_error(
    client,
    create_user_in_database,
    user_for_deletion,
    user_who_delete,
):
    await create_user_in_database(user_for_deletion)
    await create_user_in_database(user_who_delete)
    reps = client.delete(
        f"{USER_URL}?user_id={user_for_deletion['user_id']}",
        headers=await create_test_auth_headers_for_user(user_who_delete["email"]),
    )
    assert reps.status_code == 403


async def test_reject_delete_superadmin(
    client,
    create_user_in_database,
    get_user_from_database,
):
    user_data_for_deletion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_deletion)
    resp = client.delete(
        f"{USER_URL}?user_id={user_data_for_deletion["user_id"]}",
        headers=await create_test_auth_headers_for_user(
            user_data_for_deletion["email"]
        ),
    )
    assert resp.status_code == 406
    assert resp.json() == {"detail": "Superadmin cannot be deleted via API."}
    user_form_database = await get_user_from_database(user_data_for_deletion["user_id"])
    assert PortalRole.ROLE_PORTAL_SUPERADMIN in dict(user_form_database[0])["roles"]
