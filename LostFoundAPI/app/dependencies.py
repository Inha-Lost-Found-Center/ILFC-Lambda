from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import oauth2_scheme, verify_access_token
from app.db.session import get_db
from app.service import user_service
from app.models import Users

def get_current_user(
        authorization: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> Users:
    """
    토큰을 검증하고, DB에서 현재 사용자 객체를 찾아 반환하는 의존성
    (APIKeyHeader 방식: 'Bearer ' 접두사 수동 파싱)
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.split("Bearer ")[1]

    email = verify_access_token(token, credentials_exception)

    user = user_service.get_user_by_email(db, email=email)

    if user is None:
        raise credentials_exception

    return user
