import asyncio
import os
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import AsyncGenerator

import asyncpg
import pytest
import sqlalchemy
from alembic import command
from alembic.config import Config
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from api.core.config import get_settings
from api.core.dependencies import get_session
from main import app
from utils.hashing import Hasher
from utils.jwt import JWT
from utils.roles import PortalRole


settings = get_settings()

USER_URL = "/v1/users/"
LOGIN_URL = "/v1/login/"

test_engine = create_async_engine(settings.TEST_DATABASE_URL, future=True, echo=True)

test_async_session = sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)

CLEAN_TABLES = [
    "users",
]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def run_migrations():
    alembic_ini_path = os.path.join(os.getcwd(), "tests", "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)

    command.upgrade(alembic_cfg, "head")

    yield

    command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="session")
async def async_session_test():
    engine = create_async_engine(settings.TEST_DATABASE_URL, future=True, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield async_session


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(async_session_test):
    async with async_session_test() as session:
        async with session.begin():
            for table_for_cleaning in CLEAN_TABLES:
                await session.execute(
                    sqlalchemy.text(f"""TRUNCATE TABLE {table_for_cleaning};""")
                )


async def _get_test_session():
    try:
        test_engine = create_async_engine(
            settings.TEST_DATABASE_URL, future=True, echo=True
        )
        test_async_session = sessionmaker(
            test_engine, expire_on_commit=False, class_=AsyncSession
        )
        yield test_async_session()
    finally:
        pass


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[TestClient, Any]:
    """
    Create a new FastApi TestClient that uses the 'db_session' fixture to override
    the 'get_session' dependency that is injected into routers.
    """

    app.dependency_overrides[get_session] = _get_test_session
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def asyncpg_pool():
    pool = await asyncpg.create_pool(
        "".join(settings.TEST_DATABASE_URL.split("+asyncpg"))
    )
    yield pool
    await pool.close()


@pytest.fixture
async def get_user_from_database(asyncpg_pool):
    async def get_user_from_database_by_uuid(user_id: str):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetch(
                """SELECT * FROM users WHERE user_id = $1;""", user_id
            )

    return get_user_from_database_by_uuid


@pytest.fixture
async def create_user_in_database(asyncpg_pool):
    async def create_user_in_database(user: dict):
        async with asyncpg_pool.acquire() as connection:
            return await connection.execute(
                """INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                user["user_id"],
                user["name"],
                user["surname"],
                user["email"],
                user["is_active"],
                Hasher.get_password_hash(user["password"]),
                user.get("roles", [PortalRole.ROLE_PORTAL_USER]),
            )

    return create_user_in_database


async def create_test_jwt_token_for_user(email: str, token_type) -> str:
    token = await JWT.create_jwt_token(data={"sub": email}, token_type=token_type)
    return token


async def create_test_auth_headers_for_user(email: str) -> dict[str, str]:
    access_token = await create_test_jwt_token_for_user(email, "access")
    return {"Authorization": f"Bearer {access_token}"}


async def get_test_data_from_jwt_token(token: str, token_type: str) -> str:
    token_key = (
        settings.SECRET_KEY_FOR_ACCESS
        if token_type == "access"
        else settings.SECRET_KEY_FOR_REFRESH
    )
    payload = jwt.decode(token, key=token_key, algorithms=[settings.ALGORITHM])
    return payload


async def assert_token_lifetime(token_data, expected_minutes):
    exp_timestamp = token_data.get("exp")
    if exp_timestamp is None:
        return False

    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    now_datetime = datetime.now(timezone.utc)

    token_lifetime = (exp_datetime - now_datetime).total_seconds() / 60
    return expected_minutes - 5 <= token_lifetime <= expected_minutes
