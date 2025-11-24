
from pydantic import BaseModel, EmailStr
from app.users.schemas import UserRole


class Token(BaseModel):
    access_token: str
    refresh_token: str 
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str  
    role: UserRole
    type: str 


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class OTPResend(BaseModel):
    email: EmailStr

class RefreshToken(BaseModel):
    refresh_token: str