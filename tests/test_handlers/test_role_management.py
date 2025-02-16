from uuid import uuid4

import pytest

from tests.conftest import create_test_auth_headers_for_user
from tests.conftest import USER_URL
from utils.roles import PortalRole


async def test_add_admin_role_to_user_by_superadmin(
    client, create_user_in_database, get_user_from_database
):
    user_data_for_promotion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_data_who_promoted = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_promotion)
    await create_user_in_database(user_data_who_promoted)

    resp = client.patch(
        f"{USER_URL}admin_privilege/?user_id={user_data_for_promotion["user_id"]}",
        headers=await create_test_auth_headers_for_user(
            user_data_who_promoted["email"]
        ),
    )

    data_from_resp = resp.json()
    assert resp.status_code == 200
    updated_user_from_db = await get_user_from_database(
        data_from_resp["updated_user_id"]
    )
    assert len(updated_user_from_db) == 1
    updated_user_from_db = dict(updated_user_from_db[0])
    assert updated_user_from_db["user_id"] == user_data_for_promotion["user_id"]
    assert PortalRole.ROLE_PORTAL_ADMIN in updated_user_from_db["roles"]


async def test_add_admin_role_to_user_by_superadmin_invalid_id_error(
    client, create_user_in_database, get_user_from_database
):
    user_data_for_promotion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_data_who_promoted = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_promotion)
    await create_user_in_database(user_data_who_promoted)

    invalid_user_id = "123"

    resp = client.patch(
        f"{USER_URL}admin_privilege/?user_id={invalid_user_id}",
        headers=await create_test_auth_headers_for_user(
            user_data_who_promoted["email"]
        ),
    )

    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "user_id"],
                "msg": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3",
                "input": f"{invalid_user_id}",
                "ctx": {
                    "error": "invalid length: expected length 32 for simple format, found 3"
                },
            }
        ]
    }
    resp_user_from_db = await get_user_from_database(user_data_for_promotion["user_id"])

    resp_user_from_db = dict(resp_user_from_db[0])
    assert resp_user_from_db["user_id"] == user_data_for_promotion["user_id"]
    assert PortalRole.ROLE_PORTAL_ADMIN not in resp_user_from_db["roles"]


async def test_add_admin_role_to_user_by_superadmin_non_existent_id_error(
    client, create_user_in_database, get_user_from_database
):
    user_data_for_promotion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_data_who_promoted = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_promotion)
    await create_user_in_database(user_data_who_promoted)

    non_existent_user_id = uuid4()

    resp = client.patch(
        f"{USER_URL}admin_privilege/?user_id={non_existent_user_id}",
        headers=await create_test_auth_headers_for_user(
            user_data_who_promoted["email"]
        ),
    )

    assert resp.status_code == 404
    assert resp.json() == {"detail": f"User with id {non_existent_user_id} not found."}

    resp_user_from_db = await get_user_from_database(user_data_for_promotion["user_id"])

    resp_user_from_db = dict(resp_user_from_db[0])
    assert resp_user_from_db["user_id"] == user_data_for_promotion["user_id"]
    assert PortalRole.ROLE_PORTAL_ADMIN not in resp_user_from_db["roles"]


async def test_add_admin_role_to_user_by_superadmin_promote_itself_error(
    client, create_user_in_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data)

    resp = client.patch(
        f"{USER_URL}admin_privilege/?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )

    assert resp.status_code == 400
    assert resp.json() == {"detail": "Cannot manage privileges of itself."}


@pytest.mark.parametrize(
    "promoted_user_data, promoter_data, expected_status_code, expected_detail",
    [
        (
            {
                "user_id": uuid4(),
                "email": "lol1kek@mail.ru",
            },
            {"roles": [PortalRole.ROLE_PORTAL_ADMIN]},
            403,
            {"detail": "Forbidden."},
        ),
        (
            {
                "user_id": uuid4(),
                "email": "lol1kek@mail.ru",
            },
            {"roles": [PortalRole.ROLE_PORTAL_USER]},
            403,
            {"detail": "Forbidden."},
        ),
        (
            {
                "user_id": uuid4(),
                "email": "lol1kek@mail.ru",
                "roles": [PortalRole.ROLE_PORTAL_ADMIN],
            },
            {"roles": [PortalRole.ROLE_PORTAL_SUPERADMIN]},
            409,
            {
                "detail": "User with email lol1kek@mail.ru already promoted to admin / superadmin"
            },
        ),
    ],
)
async def test_invalid_admin_privilege_assignment(
    client,
    create_user_in_database,
    promoted_user_data,
    promoter_data,
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
        "roles": [PortalRole.ROLE_PORTAL_USER],
    }
    user_for_promotion_data = {**user_data, **promoted_user_data}
    user_who_promoted_data = {**user_data, **promoter_data}

    await create_user_in_database(user_for_promotion_data)
    await create_user_in_database(user_who_promoted_data)

    resp = client.patch(
        f"{USER_URL}admin_privilege/?user_id={user_for_promotion_data['user_id']}",
        headers=await create_test_auth_headers_for_user(
            user_who_promoted_data["email"]
        ),
    )

    assert resp.status_code == expected_status_code
    assert resp.json() == expected_detail


async def test_revoke_admin_role_to_user_by_superadmin(
    client, create_user_in_database, get_user_from_database
):
    user_data_for_promotion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_ADMIN],
    }
    user_data_who_promoted = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_promotion)
    await create_user_in_database(user_data_who_promoted)

    resp = client.delete(
        f"{USER_URL}admin_privilege/?user_id={user_data_for_promotion["user_id"]}",
        headers=await create_test_auth_headers_for_user(
            user_data_who_promoted["email"]
        ),
    )

    data_from_resp = resp.json()
    assert resp.status_code == 200
    updated_user_from_db = await get_user_from_database(
        data_from_resp["updated_user_id"]
    )
    assert len(updated_user_from_db) == 1
    updated_user_from_db = dict(updated_user_from_db[0])
    assert updated_user_from_db["user_id"] == user_data_for_promotion["user_id"]
    assert PortalRole.ROLE_PORTAL_ADMIN not in updated_user_from_db["roles"]


async def test_revoke_admin_role_to_user_by_superadmin_invalid_id_error(
    client, create_user_in_database, get_user_from_database
):
    user_data_for_promotion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_ADMIN],
    }
    user_data_who_promoted = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_promotion)
    await create_user_in_database(user_data_who_promoted)

    invalid_user_id = "123"

    resp = client.delete(
        f"{USER_URL}admin_privilege/?user_id={invalid_user_id}",
        headers=await create_test_auth_headers_for_user(
            user_data_who_promoted["email"]
        ),
    )

    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "user_id"],
                "msg": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3",
                "input": f"{invalid_user_id}",
                "ctx": {
                    "error": "invalid length: expected length 32 for simple format, found 3"
                },
            }
        ]
    }
    resp_user_from_db = await get_user_from_database(user_data_for_promotion["user_id"])

    resp_user_from_db = dict(resp_user_from_db[0])
    assert resp_user_from_db["user_id"] == user_data_for_promotion["user_id"]
    assert PortalRole.ROLE_PORTAL_ADMIN in resp_user_from_db["roles"]


async def test_revoke_admin_role_to_user_by_superadmin_non_existent_id_error(
    client, create_user_in_database, get_user_from_database
):
    user_data_for_promotion = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_ADMIN],
    }
    user_data_who_promoted = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data_for_promotion)
    await create_user_in_database(user_data_who_promoted)

    non_existent_user_id = uuid4()

    resp = client.delete(
        f"{USER_URL}admin_privilege/?user_id={non_existent_user_id}",
        headers=await create_test_auth_headers_for_user(
            user_data_who_promoted["email"]
        ),
    )

    assert resp.status_code == 404
    assert resp.json() == {"detail": f"User with id {non_existent_user_id} not found."}

    resp_user_from_db = await get_user_from_database(user_data_for_promotion["user_id"])

    resp_user_from_db = dict(resp_user_from_db[0])
    assert resp_user_from_db["user_id"] == user_data_for_promotion["user_id"]
    assert PortalRole.ROLE_PORTAL_ADMIN in resp_user_from_db["roles"]


async def test_revoke_admin_role_to_user_by_superadmin_promote_itself_error(
    client, create_user_in_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol1@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
        "roles": [PortalRole.ROLE_PORTAL_SUPERADMIN],
    }
    await create_user_in_database(user_data)

    resp = client.delete(
        f"{USER_URL}admin_privilege/?user_id={user_data['user_id']}",
        headers=await create_test_auth_headers_for_user(user_data["email"]),
    )

    assert resp.status_code == 400
    assert resp.json() == {"detail": "Cannot manage privileges of itself."}


@pytest.mark.parametrize(
    "promoted_user_data, promoter_data, expected_status_code, expected_detail",
    [
        (
            {
                "user_id": uuid4(),
                "email": "lol1kek@mail.ru",
            },
            {"roles": [PortalRole.ROLE_PORTAL_ADMIN]},
            403,
            {"detail": "Forbidden."},
        ),
        (
            {
                "user_id": uuid4(),
                "email": "lol1kek@mail.ru",
            },
            {"roles": [PortalRole.ROLE_PORTAL_USER]},
            403,
            {"detail": "Forbidden."},
        ),
        (
            {
                "user_id": uuid4(),
                "email": "lol1kek@mail.ru",
                "roles": [PortalRole.ROLE_PORTAL_USER],
            },
            {"roles": [PortalRole.ROLE_PORTAL_SUPERADMIN]},
            409,
            {"detail": "User with email lol1kek@mail.ru has no admin privileges"},
        ),
    ],
)
async def test_invalid_admin_privilege_revocation(
    client,
    create_user_in_database,
    promoted_user_data,
    promoter_data,
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
        "roles": [PortalRole.ROLE_PORTAL_ADMIN],
    }
    user_for_promotion_data = {**user_data, **promoted_user_data}
    user_who_promoted_data = {**user_data, **promoter_data}

    await create_user_in_database(user_for_promotion_data)
    await create_user_in_database(user_who_promoted_data)

    resp = client.delete(
        f"{USER_URL}admin_privilege/?user_id={user_for_promotion_data['user_id']}",
        headers=await create_test_auth_headers_for_user(
            user_who_promoted_data["email"]
        ),
    )

    assert resp.status_code == expected_status_code
    assert resp.json() == expected_detail
