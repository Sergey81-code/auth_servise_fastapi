from uuid import uuid4

import pytest

from utils.hashing import Hasher


async def test_create_user(client, get_user_from_database):
    user_data = {
        "name": "Nikolay",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
    }
    resp = client.post("/user/", json=user_data)
    data_from_resp = resp.json()
    assert resp.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True
    users_from_db = await get_user_from_database(data_from_resp["user_id"])
    assert len(users_from_db) == 1
    user_from_db = dict(users_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert Hasher.verify_password(
        user_data["password"], user_from_db["hashed_password"]
    )
    assert user_from_db["is_active"] is True
    assert str(user_from_db["user_id"]) == data_from_resp["user_id"]


async def test_create_user_dublicate_email_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
        "is_active": True,
    }
    user_data_same_email = {
        "name": "Nikolaii",
        "surname": "Sviridovv",
        "email": "lol@kek.com",
        "password": "Abcd12!@",
    }
    await create_user_in_database(user_data)
    resp = client.post("/user/", json=user_data_same_email)
    assert resp.status_code == 503
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in resp.json()["detail"]
    )


@pytest.mark.parametrize(
    "user_data, expected_status_code, expected_detail",
    [
        (
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "surname"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "email"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {"name": "123", "surname": "123", "email": "lol", "password": "12345"},
            422,
            {"detail": "Name should contains only letters"},
        ),
        (
            {"name": "Sergey", "surname": "123", "email": "lol", "password": "12345"},
            422,
            {"detail": "Surname should contains only letters"},
        ),
        (
            {
                "name": "Sergey",
                "surname": "Banny",
                "email": "lol",
                "password": "12345Abc@",
            },
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "lol",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
        (
            {
                "name": "Sergey",
                "surname": "Banny",
                "email": "example@gmail.com",
                "password": "12345",
            },
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {
                "name": "Sergey",
                "surname": "Banny",
                "email": "example@gmail.com",
                "password": "12345678",
            },
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {
                "name": "Sergey",
                "surname": "Banny",
                "email": "example@gmail.com",
                "password": "12345abc",
            },
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
        (
            {
                "name": "Sergey",
                "surname": "Banny",
                "email": "example@gmail.com",
                "password": "12345Abc",
            },
            422,
            {
                "detail": "Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
            },
        ),
    ],
)
async def test_create_user_validation_error(
    client,
    user_data,
    expected_status_code,
    expected_detail,
):
    resp = client.post("/user/", json=user_data)
    assert resp.status_code == expected_status_code
    resp_data = resp.json()
    assert resp_data == expected_detail
