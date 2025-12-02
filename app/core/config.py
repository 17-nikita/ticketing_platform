# in: app/core/config.py

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str 
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr

    MAIL_PORT: int 
    MAIL_SERVER: str 
    MAIL_STARTTLS: bool 
    MAIL_SSL_TLS: bool 
    TICKETMASTER_API_KEY: str

    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str  # You will get this in the last step
    DOMAIN: str = "http://localhost:8000" # Where your frontend/docs live

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cart Logic Config (Good practice to keep logic variables here too)
    # CART_REMINDER_INITIAL_HOURS: int = 1
    # CART_REMINDER_RECURRING_HOURS: int = 5
    # CART_REMINDER_RECURRING_DELAY_MINS: int = 3
    CART_INITIAL_DELAY_MINS: int = 2
    CART_FOLLOWUP_DELAY_MINS: int = 3 #mins
    CART_RECURRING_DELAY_MINS: int = 5
   


    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" 
    )


settings = Settings()