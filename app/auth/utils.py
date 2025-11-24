# hashing.py            # Passlib logic

from passlib.context import CryptContext
import random
from datetime import datetime, timedelta, timezone


pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


def generate_otp(n: int = 6) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(n)])



def otp_expiry_time(minutes: int = 10) -> datetime:
    """Returns a 'now + 10 minutes' timestamp."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

def is_otp_expired(expiry_time: datetime) -> bool:
    return datetime.now(timezone.utc) > expiry_time