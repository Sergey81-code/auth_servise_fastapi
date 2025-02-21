import re

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import field_validator

from api.core.exceptions import AppExceptions


PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_])[A-Za-z\d\W_]{8,16}$"
)


class LoginUser(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if not PASSWORD_REGEX.match(value):
            AppExceptions.unauthorized_exception(
                "Password must be 8-16 characters long, \
                                                                contain uppercase and lowercase letters, numbers, and special characters."
            )
        return value


class Token(BaseModel):
    access_token: str
    token_type: str
