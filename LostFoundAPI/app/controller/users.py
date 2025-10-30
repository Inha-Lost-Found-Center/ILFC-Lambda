from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas import user as user_schema
from app.db.session import get_db
from app.service import user_service

router = APIRouter()

# 1.7 회원 가입 API
@router.post("/register", response_model=user_schema.UserResponse)
async def create_user(
        user_in: user_schema.UserCreate,
        db: Session = Depends(get_db)
):
    """
    사용자 회원가입 (컨트롤러)
    """

    db_user = user_service.get_user_by_email(db, email=user_in.email)

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    created_user = user_service.create_new_user(db, user_in=user_in)
    return created_user

# 1.8 로그인 기능 API
@router.post("/login", response_model=user_schema.Token)
async def login_for_access_token(
        user_in: user_schema.UserLogin,
        db: Session = Depends(get_db)
):
    """
    로그인 후 Access Token 발급 (컨트롤러)
    """

    access_token = user_service.authenticate_user(db, user_in=user_in)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": access_token, "token_type": "bearer"}
