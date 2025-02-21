from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from api.core.logging.logging_app import logger


class AppExceptions:

    @staticmethod
    def bad_request_exception(message: str):
        raise HTTPException(status_code=400, detail=message)

    @staticmethod
    def unauthorized_exception(message: str = "Incorrect username or password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )

    @staticmethod
    def forbidden_exception(message: str = "Forbidden."):
        raise HTTPException(status_code=403, detail=message)

    @staticmethod
    def not_found_exception(message: str):
        raise HTTPException(status_code=404, detail=message)

    @staticmethod
    def not_acceptable_exception(message: str):
        raise HTTPException(status_code=406, detail=message)

    @staticmethod
    def conflict_exception(message: str):
        raise HTTPException(status_code=409, detail=message)

    @staticmethod
    def validation_exception(message: str):
        raise HTTPException(status_code=422, detail=message)

    @staticmethod
    def service_unavailable_exception(message: str):
        raise HTTPException(status_code=503, detail=message)


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f"HTTP Exception: {exc.detail}, Status: {exc.status_code}, Path: {request.url}"
    )
    return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
