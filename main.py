import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRouter

from api.auth.handlers import login_router
from api.users.handlers import user_router

app = FastAPI(title="my-fastapi")

main_api_router = APIRouter()

main_api_router.include_router(user_router, prefix="/user", tags=["user"])
main_api_router.include_router(login_router, prefix="/login", tags=["login"])
app.include_router(main_api_router)

if __name__ == "__main__":
    # run app on the host and port
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
