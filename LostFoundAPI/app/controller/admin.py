from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.service import manager_service
from app.schemas import manager as manager_schema
from app.schemas import user as user_schema # Token 스키마 재사용 (또는 새로 정의)
from app.core import security
from app.dependencies import get_current_admin
from app.models.manager import Managers

router = APIRouter()

# 관리자 로그인 (JWT 발급)
@router.post("/login", response_model=user_schema.Token)
async def login_admin(
        login_data: manager_schema.ManagerLogin,
        db: Session = Depends(get_db)
):
    manager = manager_service.authenticate_manager(db, login_data)

    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": manager.email, "role": "admin"}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=manager_schema.ManagerResponse)
async def read_admin_me(
        current_admin: Managers = Depends(get_current_admin)
):
    return current_admin
