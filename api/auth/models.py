import re
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, field_validator


PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_])[A-Za-z\d\W_]{8,16}$")

class LoginUser(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if not PASSWORD_REGEX.match(value):
            raise HTTPException(
                status_code=422, detail="Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters."
                )
        return value
    
class Token(BaseModel):
    access_token: str
    token_type: str