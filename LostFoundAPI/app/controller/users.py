from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas import user as user_schema
from app.models import Users
from app.db.session import get_db
from app.core import security

router = APIRouter()

# 1.7 회원 가입 API
@router.post("/register", response_model=user_schema.UserResponse)
async def create_user(
        user_in: user_schema.UserCreate,
        db: Session = Depends(get_db)
):
    """
    사용자 회원가입
    - **email**: 유저 이메일 (ID)
    - **password**: 유저 비밀번호
    - **name**: 유저 이름
    - **contact_info**: (선택) 연락처
    """

    # (이하 로직은 동일)
    db_user = db.query(Users).filter(Users.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = security.get_password_hash(user_in.password)

    db_user = Users(
        email=user_in.email,
        hashed_password=hashed_password,
        name=user_in.name,
        contact_info=user_in.contact_info
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

# 1.8 로그인 기능 API
@router.post("/login", response_model=user_schema.Token)
async def login_for_access_token(
        user_in: user_schema.UserLogin,
        db: Session = Depends(get_db)
):
    """
    로그인 후 Access Token 발급
    (JSON으로 email과 password를 받습니다)
    """

    user = db.query(Users).filter(Users.email == user_in.email).first()

    if not user or not security.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": user.email}
    )

    return {"access_token": access_token, "token_type": "bearer"}
