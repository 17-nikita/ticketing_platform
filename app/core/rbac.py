from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.users.models import User
from app.users.enums import UserRole
from app.auth import jwt 
from app.users.services import UserService 

oauth2_scheme = HTTPBearer()

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)) -> User:
    token = auth.credentials  
    token_data = jwt.decode_token(token, expected_type="access")
    user = await UserService.get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user. Please verify your email."
        )
        
    return user


def get_current_user_with_role(role: UserRole):  
    async def role_checker(user: User = Depends(get_current_user) ) -> User:
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission! Requires role: {role.value}"
            )
        return user
    return role_checker