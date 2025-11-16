# # in: app/core/rbac.py
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.core.database import get_db
# from app.users.services import UserService 
# from app.users.models import User
# from app.users.enums import UserRole
# from app.auth import jwt

# # This points to your login endpoint
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# """ Dependency to get the current user from an ACCESS token."""
# async def get_current_user(token: str = Depends(oauth2_scheme),  db: AsyncSession = Depends(get_db)) -> User:
    
#     token_data = jwt.decode_token(token, expected_type="access")
    
#     user = await UserService.get_user_by_email(db, email=token_data.sub)
    
#     if user is None:
#         raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    
#     if not user.is_verified:
#         raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inactive user")
        
#     return user


# # def get_current_user_with_role(role: UserRole):
# #     async def role_checker(user: User = Depends(get_current_user)) -> User:
# #         if user.role != role:
# #             raise HTTPException(
# #                 status.HTTP_403_FORBIDDEN,
# #                 detail=f"You do not have permission! Requires role: {role.value}"
# #             )
# #         return user
        
# #     return role_checker