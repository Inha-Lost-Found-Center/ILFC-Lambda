from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import oauth2_scheme, verify_access_token
from app.db.session import get_db
from app.service import user_service
from app.models import Users
from app.models.manager import Managers, ManagerRole

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

def get_current_admin(
        authorization: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> Managers:
    """
    토큰을 검증하고, 현재 요청한 사용자가 '관리자(Manager)'인지 확인합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.split("Bearer ")[1]

    email = verify_access_token(token, credentials_exception)

    manager = db.query(Managers).filter(Managers.email == email).first()

    if manager is None:
        raise credentials_exception

    if not manager.is_active:
        raise HTTPException(status_code=400, detail="Inactive admin account")

    return manager

# 최고 관리자(ADMIN)만 접근 가능한 의존성 추가
def get_super_admin(
        current_admin: Managers = Depends(get_current_admin)
) -> Managers:
    if current_admin.role != ManagerRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_admin
