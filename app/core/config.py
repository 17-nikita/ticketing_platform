from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr

# BaseSettings- It's the class you inherit from to define what your settings are
# SettingsConfigDict - It's the object you use to configure how BaseSettings loads those variables from env file
class Settings(BaseSettings):
 
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- Email Service (fastapi-mail / SendGrid) ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    
    # Tell Pydantic to load from a .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra fields
    )

settings = Settings()