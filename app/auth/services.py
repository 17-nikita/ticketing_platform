import logging  # <--- Added import
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.exceptions import CustomError
from app.users.models import User
from app.users.services import UserService 
from app.users.schemas import UserCreate
from app.users.enums import UserRole
from app.auth import jwt
from app.auth.schemas import Token, OTPVerify, RefreshToken
from app.services.email import send_otp_email, send_welcome_email
from app.auth.utils import (
    generate_otp,
    otp_expiry_time,
    is_otp_expired,
    hash_password,
    verify_password
)

# <--- Initialize Logger
logger = logging.getLogger(__name__) 

class AuthService:

    @staticmethod
    async def register_user(db: AsyncSession, payload: UserCreate):    
        logger.info(f"Attempting to register user with email: {payload.email}") # <--- Log entry

        existing = await UserService.get_user_by_email(db, payload.email)
        if existing:
            logger.warning(f"Registration failed: Email {payload.email} already exists.") # <--- Log failure
            raise CustomError(message="Email already registered", status_code=status.HTTP_400_BAD_REQUEST)

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
        
        logger.info(f"User registered successfully: {payload.email}. OTP sent.") # <--- Log success
        return {"message": "User registered. OTP sent to email."}


    @staticmethod
    async def verify_user_otp(db: AsyncSession, payload: OTPVerify) -> Token:    
        logger.info(f"Verifying OTP for user: {payload.email}") # <--- Log entry

        user = await UserService.get_user_by_email(db, payload.email)
        if not user:
            logger.warning(f"OTP Verification failed: User {payload.email} not found.") # <--- Log failure
            raise CustomError(message="User not found", status_code=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            logger.warning(f"OTP Verification failed: User {payload.email} is already verified.") # <--- Log failure
            raise CustomError(message="User is already verified.", status_code=status.HTTP_400_BAD_REQUEST)

        if is_otp_expired(user.otp_expires_at):
            logger.warning(f"OTP Verification failed: OTP expired for {payload.email}.") # <--- Log failure
            raise CustomError(message="OTP expired", status_code=status.HTTP_400_BAD_REQUEST)

        if payload.otp != user.otp_code:
            logger.warning(f"OTP Verification failed: Invalid OTP code provided for {payload.email}.") # <--- Log failure
            raise CustomError(message="Invalid OTP", status_code=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        await db.commit()
        await send_welcome_email(user.email)
        
        access_token = jwt.create_access_token(email=user.email, role=user.role)
        refresh_token = jwt.create_refresh_token(email=user.email, role=user.role)
        
        logger.info(f"OTP verified successfully for {payload.email}. Tokens generated.") # <--- Log success
        return Token(access_token=access_token, refresh_token=refresh_token)


    @staticmethod
    async def login_user(db: AsyncSession, form_data: OAuth2PasswordRequestForm) -> Token:    
        logger.info(f"Login attempt for user: {form_data.username}") # <--- Log entry
        
        user = await UserService.get_user_by_email(db, form_data.username)
        if not user:
            logger.warning(f"Login failed: User {form_data.username} not found.") # <--- Log failure
            raise CustomError(message="Invalid email or password", status_code=status.HTTP_400_BAD_REQUEST)

        if not verify_password(form_data.password, user.password_hash):
            logger.warning(f"Login failed: Invalid password for {form_data.username}.") # <--- Log failure
            raise CustomError(message="Invalid email or password", status_code=status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            logger.warning(f"Login failed: User {form_data.username} is not verified.") # <--- Log failure
            raise CustomError(message="Email is not verified.", status_code=status.HTTP_400_BAD_REQUEST)

        access_token = jwt.create_access_token(email=user.email, role=user.role)
        refresh_token = jwt.create_refresh_token(email=user.email, role=user.role)   
        
        logger.info(f"User {form_data.username} logged in successfully.") # <--- Log success
        return Token(access_token=access_token, refresh_token=refresh_token)


    @staticmethod
    async def resend_otp(db: AsyncSession, email: str):     
        logger.info(f"Request to resend OTP for: {email}") # <--- Log entry

        user = await UserService.get_user_by_email(db, email)
        if not user:
            logger.warning(f"Resend OTP failed: User {email} not found.") # <--- Log failure
            raise CustomError(message="User not found", status_code=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            logger.warning(f"Resend OTP failed: User {email} is already verified.") # <--- Log failure
            raise CustomError(message="User already verified", status_code=status.HTTP_400_BAD_REQUEST)

        user.otp_code = generate_otp() 
        user.otp_expires_at = otp_expiry_time()

        await db.commit()

        await send_otp_email(user.email, user.otp_code) 

        logger.info(f"New OTP resent successfully to {email}.") # <--- Log success
        return {"message": "New OTP sent successfully."}
    

    @staticmethod
    async def refresh_access_token(db: AsyncSession, token_data: RefreshToken) -> Token:
        # Note: We don't log the actual token for security, just the action
        logger.debug("Attempting to refresh access token.") # <--- Log entry

        token_payload = jwt.decode_token(
            token_data.refresh_token, 
            expected_type="refresh")
        
        user = await UserService.get_user_by_email(db, token_payload.sub)
        
        if not user or not user.is_verified:
            logger.warning(f"Token refresh failed: User {token_payload.sub} invalid or unverified.") # <--- Log failure
            raise CustomError(message="Could not validate user", status_code=401)
        
        access_token = jwt.create_access_token(email=user.email, role=user.role)
        refresh_token = jwt.create_refresh_token(email=user.email, role=user.role)
        
        logger.info(f"Access token refreshed successfully for user: {user.email}") # <--- Log success
        return Token(access_token=access_token, refresh_token=refresh_token)