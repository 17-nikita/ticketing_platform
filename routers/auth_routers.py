from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.throttling import limiter
from app.users.schemas import UserCreate
from app.auth.schemas import Token, OTPVerify, OTPResend,RefreshToken
from app.auth.services import AuthService 

router = APIRouter(prefix="/auth",tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/10minutes")
async def register(request: Request,payload: UserCreate, db: AsyncSession = Depends(get_db)):
    return await AuthService.register_user(db, payload)


@router.post("/verify-otp", response_model=Token)
@limiter.limit("5/10minutes")
async def verify_otp(request: Request,payload: OTPVerify,db: AsyncSession = Depends(get_db)):
    return await AuthService.verify_user_otp(db, payload)


@router.post("/login", response_model=Token)
@limiter.limit("15/5minutes")
async def login(request: Request,form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await AuthService.login_user(db, form_data)


@router.post("/resend-otp")
@limiter.limit("5/10minutes")
async def resend_otp(request: Request,payload: OTPResend, db: AsyncSession = Depends(get_db)):
    return await AuthService.resend_otp(db, payload.email)

#Get a new Access and Refresh token pair.
@router.post("/refresh-token", response_model=Token)
@limiter.limit("10/minute")
async def refresh_token(request: Request,payload: RefreshToken, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_access_token(db, payload)