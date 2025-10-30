from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings # .env에서 읽어온 설정값

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

oauth2_scheme = APIKeyHeader(name="Authorization")

def verify_access_token(token: str, credentials_exception: HTTPException):
    """
    JWT 토큰을 검증하고, 유효하면 payload(sub: email)를 반환합니다.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

        return email

    except JWTError:
        raise credentials_exception
