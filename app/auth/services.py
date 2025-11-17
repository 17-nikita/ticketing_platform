# in: app/auth/services.py
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.users.models import User
from app.users.services import UserService 
from app.users.schemas import UserCreate
from app.users.enums import UserRole
from app.auth import jwt
from app.auth.schemas import Token, OTPVerify,RefreshToken
from app.services.email import send_otp_email, send_welcome_email
from app.auth.utils import (
    generate_otp,
    otp_expiry_time,
    is_otp_expired,
    hash_password,
    verify_password
)

class AuthService:

    @staticmethod
    async def register_user(db: AsyncSession, payload: UserCreate):    
        existing = await UserService .get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            is_verified=False,
            role=payload.role 
        )
        db.add(user)
        await db.commit() 

        user.otp_code = generate_otp() 
        user.otp_expires_at = otp_expiry_time()

        await db.commit() 
        await db.refresh(user)

        await send_otp_email(user.email, user.otp_code)
        return {"message": "User registered. OTP sent to email."}


    @staticmethod
    async def verify_user_otp(db: AsyncSession, payload: OTPVerify) -> Token:    
        user = await UserService.get_user_by_email(db, payload.email)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        if user.is_verified:
             raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is already verified.")

        if is_otp_expired(user.otp_expires_at):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "OTP expired")

        if payload.otp != user.otp_code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OTP")

        user.is_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        await db.commit()

        await send_welcome_email(user.email)

        # Log them in and return tokens
        access_token = jwt.create_access_token(email=user.email, role=user.role)
        refresh_token = jwt.create_refresh_token(email=user.email, role=user.role)

        return Token(access_token=access_token, refresh_token=refresh_token)


    @staticmethod
    async def login_user(db: AsyncSession, form_data: OAuth2PasswordRequestForm) -> Token:
        
        user = await UserService.get_user_by_email(db, form_data.username)
        if not user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email or password")

        if not verify_password(form_data.password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email or password")

        if not user.is_verified:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email is not verified.")

        access_token = jwt.create_access_token(email=user.email, role=user.role)
        refresh_token = jwt.create_refresh_token(email=user.email, role=user.role)
        
        return Token(access_token=access_token, refresh_token=refresh_token)


    @staticmethod
    async def resend_otp(db: AsyncSession, email: str):     
        user = await UserService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        if user.is_verified:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User already verified")

        user.otp_code = generate_otp() 
        user.otp_expires_at = otp_expiry_time()

        await db.commit()

        await send_otp_email(user.email, user.otp_code) 

        return {"message": "New OTP sent successfully."}
    


    @staticmethod
    async def refresh_access_token(db: AsyncSession, token_data: RefreshToken) -> Token:
        token_payload = jwt.decode_token(
            token_data.refresh_token, 
            expected_type="refresh")
        
        user = await UserService.get_user_by_email(db, token_payload.sub)
        
        if not user or not user.is_verified:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, 
                "Could not validate user"
            )
        
        # 3. Issue a new pair of tokens
        access_token = jwt.create_access_token(email=user.email, role=user.role)
        refresh_token = jwt.create_refresh_token(email=user.email, role=user.role)
        
        return Token(access_token=access_token, refresh_token=refresh_token)