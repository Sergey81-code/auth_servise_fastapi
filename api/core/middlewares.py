from fastapi import Request
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.core.logging.logging_app import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            logger.info(f"Request: {request.method} {request.url}")
            response: Response = await call_next(request)
            if response.status_code < 400:
                logger.info(
                    f"Response: {response.status_code} for {request.method} {request.url}"
                )
        except Exception as exc:
            logger.error(f"Exception occurred: {exc}", exc_info=True)
            raise exc

        return response
