from functools import lru_cache

from pydantic_settings import BaseSettings

import settings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Auth Service"
    VERSION: str = "1.0.0"

    DATABASE_URL: str = settings.REAL_DATABASE_URL
    TEST_DATABASE_URL: str = settings.TEST_DATABASE_URL

    APP_PORT: int = settings.APP_PORT

    SECRET_KEY_FOR_ACCESS: str = settings.SECRET_KEY_FOR_ACCESS
    SECRET_KEY_FOR_REFRESH: str = settings.SECRET_KEY_FOR_REFRESH
    ALGORITHM: str = settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS: int = settings.REFRESH_TOKEN_EXPIRE_DAYS


@lru_cache()
def get_settings():
    return Settings()
