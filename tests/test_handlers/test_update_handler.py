import asyncio
from uuid import uuid4

import pytest

from utils.hashing import Hasher


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
        f"/user/?user_id={user_data['user_id']}", json=user_data_updated
    )
    hashed_password = Hasher.get_password_hash(user_data_updated["new_password"])
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
    assert user_from_db["hashed_password"] == hashed_password
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

    user1_update_data = {"name": "name", "surname": "surname", "email": "email@mail.ru"}

    created_request = [
        create_user_in_database(user_data) for user_data in [user1, user2, user3]
    ]

    await asyncio.gather(*created_request)

    resp = client.patch(f"/user/?user_id={user1['user_id']}", json=user1_update_data)
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
    assert user1_from_db["is_active"] is user1["is_active"]

    assert user2_from_db["user_id"] == user2["user_id"]
    assert user2_from_db["name"] == user2["name"]
    assert user2_from_db["surname"] == user2["surname"]
    assert user2_from_db["email"] == user2["email"]
    assert user2_from_db["is_active"] is user2["is_active"]

    assert user3_from_db["user_id"] == user3["user_id"]
    assert user3_from_db["name"] == user3["name"]
    assert user3_from_db["surname"] == user3["surname"]
    assert user3_from_db["email"] == user3["email"]
    assert user3_from_db["is_active"] is user3["is_active"]


@pytest.mark.parametrize(
    "user_data_updated, expected_status_code, expected_detail",
    [
        (
            {},
            422,
            {
                "detail": "At least one parameter for user update info should be proveded"
            },
        ),
        ({"name": "123"}, 422, {"detail": "Name should contains only letters"}),
        ({"surname": "123"}, 422, {"detail": "Surname should contains only letters"}),
        (
            {"email": "123"},
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
            {"email": ""},
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
        ({"name": ""}, 422, {"detail": "Name should contains only letters"}),
        ({"surname": ""}, 422, {"detail": "Surname should contains only letters"}),
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
        f"/user/?user_id={user_data['user_id']}", json=user_data_updated
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
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    resp = client.patch(
        "/user/?user_id=123",
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
    }
    await create_user_in_database(user_data)
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    user_id_for_finding = uuid4()
    resp = client.patch(
        f"/user/?user_id={user_id_for_finding}",
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
        "email": user_data2["email"],
    }
    resp = client.patch(
        f"/user/?user_id={user_data1['user_id']}",
        json=user_data_dublicate_email,
    )
    assert resp.status_code == 503
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in resp.json()["detail"]
    )
