import asyncio
import os
import subprocess
import sys
from typing import Any
from typing import AsyncGenerator

import asyncpg
import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

import settings
from db.session import get_db
from main import app
from utils.hashing import Hasher


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
    alembic_cmd = "alembic"

    if sys.platform == "win32":
        alembic_cmd = os.path.join(os.getcwd(), "venv", "Scripts", "alembic.exe")

    migrations_dir = os.path.join(os.getcwd(), "tests", "migrations")
    alembic_ini_path = os.path.join(os.getcwd(), "tests", "alembic.ini")

    if not os.path.exists(migrations_dir):
        subprocess.run([alembic_cmd, "init", migrations_dir], check=True)

    subprocess.run(
        [
            alembic_cmd,
            "-c",
            alembic_ini_path,
            "revision",
            "--autogenerate",
            "-m",
            '"test running migrations"',
        ],
        check=True,
    )

    subprocess.run(
        [alembic_cmd, "-c", alembic_ini_path, "upgrade", "heads"], check=True
    )


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


async def _get_test_db():
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
    the 'get_db' dependency that is injected into routers.
    """

    app.dependency_overrides[get_db] = _get_test_db
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
                """INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6)""",
                user["user_id"],
                user["name"],
                user["surname"],
                user["email"],
                user["is_active"],
                Hasher.get_password_hash(user["password"]),
            )

    return create_user_in_database
