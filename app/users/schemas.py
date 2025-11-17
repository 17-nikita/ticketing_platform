# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.users.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    role: UserRole
   
    class Config:
        from_attributes = True


# For changing your own password
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# For deleting your own account
class AccountDelete(BaseModel):
    current_password: str



# class UserVerify(BaseModel):
#     email: EmailStr
#     otp: str

# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str