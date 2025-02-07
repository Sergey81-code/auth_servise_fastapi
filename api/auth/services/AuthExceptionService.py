from fastapi import HTTPException
from fastapi import status


class AuthExceptionService:

    @staticmethod
    def credentials_exception(message: str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )

    @staticmethod
    def unauthorized_exception(message: str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
