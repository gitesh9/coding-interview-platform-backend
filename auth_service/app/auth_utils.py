from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Replace with an env var in production!
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a hashed one.
    Returns True if match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict[str, Any], expires_delta: timedelta = timedelta(minutes=15)) -> str: # type: ignore
    """
    Creates a JWT access token with an expiration time.
    """
    to_encode: Dict[str, Any] = data.copy()
    expire: datetime = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt