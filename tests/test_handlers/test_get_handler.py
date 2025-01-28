from uuid import uuid4

async def test_get_user(client, create_user_in_database):
    user_data = {
        'user_id': uuid4(),
        'name': 'Nikolai',
        'surname': 'Sviridov',
        'email': 'lol@kek.com',
        'is_active': True
    }
    await create_user_in_database(user_data)
    resp = client.get(f'/user/?user_id={user_data['user_id']}')
    assert resp.status_code == 200
    user_from_response = resp.json()
    assert user_from_response['user_id'] == str(user_data['user_id'])
    assert user_from_response['name'] == user_data['name']
    assert user_from_response['surname'] == user_data['surname']
    assert user_from_response['email'] == user_data['email']
    assert user_from_response['is_active'] is user_data['is_active']



async def test_get_user_id_validation_error(client):
    resp = client.get("/user/?user_id=123")
    assert resp.status_code == 422
    data_from_response = resp.json()
    assert data_from_response == {
            "detail": [
                {
                    "type": "uuid_parsing",
                    "loc": [
                        "query",
                        "user_id"
                    ],
                    "msg": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3",
                    "input": "123",
                    "ctx": {
                        "error": "invalid length: expected length 32 for simple format, found 3"
                    }
                }
            ]
        }


async def test_get_user_not_found_error(client):
    user_id = uuid4()
    resp = client.get(f"/user/?user_id={user_id}")
    assert resp.status_code == 404
    data_from_response = resp.json()
    assert data_from_response == {
            "detail": f"User with id {user_id} not found."
        }
    
