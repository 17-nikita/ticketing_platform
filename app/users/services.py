from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.users.models import User
from app.users.schemas import PasswordChange, AccountDelete
from app.auth.utils import verify_password, hash_password

class UserService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()


    @staticmethod
    async def update_user(db: AsyncSession, user: User) -> User:
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User):
        await db.delete(user)
        await db.commit()


    @staticmethod
    async def change_password(db: AsyncSession, *, user: User, payload: PasswordChange) -> dict:
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect current password")
        
        user.password_hash = hash_password(payload.new_password)
        await UserService.update_user(db, user) 
        return {"message": "Password changed successfully"}

    @staticmethod
    async def delete_account(db: AsyncSession, *, user: User, payload: AccountDelete):
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password")
        
        await UserService.delete_user(db, user) 
        return {"message": "Account deleted successfully"}