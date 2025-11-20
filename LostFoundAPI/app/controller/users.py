from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.schemas import user as user_schema
from app.db.session import get_db
from app.service import user_service
from app.service import verification_service, email_service
from app.core.config import settings

router = APIRouter()

# ============================================================
# 개발용 회원 가입 API
# ============================================================
@router.post("/register", response_model=user_schema.UserResponse)
async def create_user(
        user_in: user_schema.UserCreate,
        db: Session = Depends(get_db)
):
    """
    사용자 회원가입 (컨트롤러, 개발용)
    초기 사용자 회원가입 API 입니다. 차후 이메일이 인증된 API로 변경해주세요
    """

    db_user = user_service.get_user_by_email(db, email=user_in.email)

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    created_user = user_service.create_new_user(db, user_in=user_in)
    return created_user

# ============================================================
# 이메일 인증 후 회원 가입하는 API
# ============================================================
@router.post("/register/verified", response_model=user_schema.UserResponse)
async def create_user_verified(
        user_in: user_schema.UserCreateVerified,
        db: Session = Depends(get_db)
):
    """
    이메일 인증 토큰을 검증한 후 회원을 생성합니다.
    실제 운영 환경에서는 해당 API를 사용해주세요.
    """

    try:
        payload = jwt.decode(
            user_in.verification_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        token_email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if token_type != "verification_complete":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰 타입입니다."
            )

        if token_email != user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="인증된 이메일과 입력한 이메일이 일치하지 않습니다."
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 만료되었거나 유효하지 않습니다."
        )

    if user_service.get_user_by_email(db, email=user_in.email):
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
