import logging # <--- Added import
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.users.models import User
from app.users.schemas import PasswordChange, AccountDelete
from app.auth.utils import verify_password, hash_password
from app.core.exceptions import CustomError

# <--- Initialize Logger
logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        logger.debug(f"Searching for user by email: {email}") # <--- Log entry (Debug level)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if user:
            logger.debug(f"User found: {user.id}")
        else:
            logger.debug(f"User not found for email: {email}")
            
        return user


    @staticmethod
    async def update_user(db: AsyncSession, user: User) -> User:
        logger.debug(f"Persisting updates for user {user.id}") # <--- Log entry
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User):
        logger.warning(f"Hard deleting user {user.id} from database") # <--- Log critical action
        await db.delete(user)
        await db.commit()


    @staticmethod
    async def change_password(db: AsyncSession, *, user: User, payload: PasswordChange) -> dict:
        logger.info(f"Password change requested for user {user.id}") # <--- Log entry
        
        if not verify_password(payload.current_password, user.password_hash):
            logger.warning(f"Password change failed for user {user.id}: Incorrect current password provided") # <--- Log failure
            raise CustomError(message="Incorrect current password", status_code=status.HTTP_400_BAD_REQUEST)
        
        user.password_hash = hash_password(payload.new_password)
        await UserService.update_user(db, user) 
        
        logger.info(f"Password changed successfully for user {user.id}") # <--- Log success
        return {"message": "Password changed successfully"}

    @staticmethod
    async def delete_account(db: AsyncSession, *, user: User, payload: AccountDelete):
        logger.info(f"Account deletion requested for user {user.id}") # <--- Log entry
        
        if not verify_password(payload.current_password, user.password_hash):
            logger.warning(f"Account deletion failed for user {user.id}: Incorrect password provided") # <--- Log failure
            raise CustomError(message="Incorrect password", status_code=status.HTTP_400_BAD_REQUEST)    
        
        await UserService.delete_user(db, user) 
        
        logger.info(f"Account deleted successfully for user {user.id}") # <--- Log success
        return {"message": "Account deleted successfully"}