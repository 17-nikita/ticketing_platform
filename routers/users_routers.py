from fastapi import APIRouter, Depends, status,Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import get_current_user
from app.users.models import User
from app.users.schemas import (
    UserRead, 
    PasswordChange, 
    AccountDelete)
from app.users.services import UserService
from app.core.throttling import limiter


router = APIRouter(prefix="/users",tags=["Profile Management"])

@router.get("/me", response_model=UserRead)
@limiter.limit("30/minute")
async def read_users_me(request: Request,current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me/change_password")
@limiter.limit("3/minute")
async def change_user_password(request: Request,payload: PasswordChange,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)):
    return await UserService.change_password(
        db=db, user=current_user, payload=payload)


@router.delete("/me/delete_profile", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def delete_user_account(
    request: Request,
    payload: AccountDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    return await UserService.delete_account(
        db=db, user=current_user, payload=payload)