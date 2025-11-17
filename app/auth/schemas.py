
from pydantic import BaseModel, EmailStr
from app.users.schemas import UserRole

# This is what we return on a successful login or verification
class Token(BaseModel):
    access_token: str
    refresh_token: str 
    token_type: str = "bearer"

# This is the payload we embed in the JWT
class TokenData(BaseModel):
    sub: str  # email
    role: UserRole
    type: str # 'access' or 'refresh'


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

# Schema for resending OTP
class OTPResend(BaseModel):
    email: EmailStr

# Schema for refreshing a token
class RefreshToken(BaseModel):
    refresh_token: str