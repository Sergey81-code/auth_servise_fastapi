import re
import uuid
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import field_validator


LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_])[A-Za-z\d\W_]{8,16}$"
)


class TunedModel(BaseModel):
    class ConfigDict:
        from_attributes = True


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str

    @field_validator("name")
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @field_validator("surname")
    def validate_surname(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Surname should contains only letters"
            )
        return value

    @field_validator("password")
    def validate_password(cls, value):
        if not PASSWORD_REGEX.match(value):
            raise HTTPException(
                status_code=422,
                detail="Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters.",
            )
        return value


class DeleteUserResponse(BaseModel):
    deleted_user_id: uuid.UUID


class ActivateUserResponse(BaseModel):
    activated_user_id: uuid.UUID


class UpdatedUserResponse(BaseModel):
    updated_user_id: uuid.UUID


class UpdateUserRequest(BaseModel):
    old_password: str
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    new_password: str = None

    @field_validator("name")
    def validator_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @field_validator("surname")
    def validator_surname(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Surname should contains only letters"
            )
        return value
    

    @field_validator("new_password")
    def validate_new_password(cls, value):
        if not PASSWORD_REGEX.match(value):
            raise HTTPException(
                status_code=422,
                detail="Password must be 8-16 characters long, contain uppercase and lowercase letters, numbers, and special characters.",
            )
        return value
