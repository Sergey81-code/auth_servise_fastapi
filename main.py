import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException

from api.core.config import get_settings
from api.core.exceptions import AppExceptions
from api.core.exceptions import http_exception_handler
from api.core.middlewares import LoggingMiddleware
from api.routers import router

settings = get_settings()

app = FastAPI(title="my-fastapi")
app.add_middleware(LoggingMiddleware)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(router)


@app.get("/")
async def ping():
    AppExceptions.forbidden_exception()
    return {"Success": True}


if __name__ == "__main__":
    # run app on the host and port
    uvicorn.run("main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
