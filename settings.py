from envparse import Env

env = Env()

REAL_DATABASE_URL = env.str(
    "REAL_DATABASE_URL",
    default="postgresql+asyncpg://postgres:postgres@host.docker.internal:5431/postgres",
)
APP_PORT = env.int("APP_PORT", default=8000)

SECRET_KEY_FOR_ACCESS: str = env.str(
    "SECRET_KEY_FOR_ACCESS", default="your-strong-access-secret-key"
)
SECRET_KEY_FOR_REFRESH: str = env.str(
    "SECRET_KEY_FOR_REFRESH", default="your-strong-refresh-secret-key"
)
ALGORITHM: str = env.str("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = env.int("ACCESS_TOKEN_EXPIRE_MINUTES", default=30)
REFRESH_TOKEN_EXPIRE_DAYS: int = env.int("ACCESS_TOKEN_EXPIRE_MINUTES", default=10)

TEST_DATABASE_URL = env.str(
    "TEST_DATABASE_URL",
    default="postgresql+asyncpg://postgres_test:postgres_test@host.docker.internal:5433/postgres_test",
)  # connect string for the test database
