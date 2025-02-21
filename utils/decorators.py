from functools import wraps

from api.core.exceptions import AppExceptions
from db.models import User


def only_superadmin(func):
    @wraps(func)
    async def wrap(*args, **kwargs):
        current_user: User | None = kwargs.get("current_user")
        if not current_user or not current_user.is_superadmin:
            AppExceptions.forbidden_exception()
        return await func(*args, **kwargs)

    return wrap
