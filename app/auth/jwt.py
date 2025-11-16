from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pydantic import ValidationError
from fastapi import HTTPException, status
from app.core.config import settings
from app.auth.schemas import TokenData
from app.users.enums import UserRole

# This is the standard error for an invalid token
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(email: str, role: UserRole) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": email,
        "role": role.value,
        "exp": expire,
        "type": "refresh" 
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) 
    return encoded_jwt


def create_refresh_token(email: str, role: UserRole) -> str:
    expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": email,
        "role": role.value,
        "exp": expire,
        "type": "refresh" 
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)



def decode_token(token: str, expected_type: str) -> TokenData:
    try:
        
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
     
        email: str = payload.get("sub")
        role_str: str = payload.get("role")
        token_type: str = payload.get("type")
        
        #  Check for missing claims
        if email is None or role_str is None or token_type is None:
            raise credentials_exception
            
        #  Check if it's the right type of token
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected '{expected_type}'"
            )
        
        # Validate the role and data shape using Pydantic
        token_data = TokenData(sub=email, role=role_str, type=token_type)
        return token_data
        
    except jwt.ExpiredSignatureError:
        # Handle expired tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, ValidationError):
        # Handle all other invalid token errors
        raise credentials_exception