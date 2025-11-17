from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import get_current_user
from app.users.models import User
from app.users.schemas import (
    UserRead, 
    PasswordChange, 
    AccountDelete)
from app.users.services import UserService

router = APIRouter(prefix="/users",tags=["Profile Management"])

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me/change_password")
async def change_user_password(payload: PasswordChange,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)):
    return await UserService.change_password(
        db=db, user=current_user, payload=payload)


@router.delete("/me/delete_profile", status_code=status.HTTP_200_OK)
async def delete_user_account(
    payload: AccountDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    return await UserService.delete_account(
        db=db, user=current_user, payload=payload)