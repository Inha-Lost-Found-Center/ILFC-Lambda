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
@router.post(
    "/register",
    response_model=user_schema.UserResponse,
    summary="[개발용] 회원가입 (인증 없음)",
    description="""
    **[개발용]** 이메일 인증 절차를 건너뛰고 즉시 회원을 생성합니다.
    
    - **주의**: 실제 서비스 배포 시에는 사용하지 마세요.
    - 중복된 이메일로 가입을 시도하면 400 에러를 반환합니다.
    """,
    responses={
        400: {"description": "이미 가입된 이메일입니다."}
    }
)
async def create_user(
        user_in: user_schema.UserCreate,
        db: Session = Depends(get_db)
):
    db_user = user_service.get_user_by_email(db, email=user_in.email)

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    created_user = user_service.create_new_user(db, user_in=user_in)
    return created_user

# ============================================================
# 이메일 인증번호 발송 API
# ============================================================
@router.post(
    "/email/request-verification",
    summary="이메일 인증번호 발송 요청",
    description="""
    사용자가 입력한 이메일로 **6자리 인증 번호**를 발송합니다.
    
    - 인증 번호의 유효 시간은 **5분**입니다.
    - 이미 가입된 이메일이라면 400 에러를 반환합니다.
    - 이메일 발송에 실패하면 500 에러를 반환합니다.
    """,
    responses={
        400: {"description": "이미 가입된 이메일"},
        500: {"description": "이메일 발송 실패 또는 서버 오류"}
    }
)
async def request_email_verification(
        request: user_schema.EmailRequest,
        db: Session = Depends(get_db)
):
    if user_service.check_email_exists(db, request.email):
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    code = verification_service.create_verification_code(request.email)
    if not code:
        raise HTTPException(status_code=500, detail="서버 오류: 인증 코드 생성 실패")

    if not email_service.send_verification_email(request.email, code):
        raise HTTPException(status_code=500, detail="이메일 발송 실패")

    return {"message": "인증 번호가 발송되었습니다."}


# ============================================================
# 인증번호 검증 및 토큰 발급 API
# ============================================================
@router.post(
    "/email/verify",
    response_model=user_schema.VerificationResponse,
    summary="인증번호 검증 및 토큰 발급",
    description="""
    이메일로 전송된 인증 번호를 검증합니다.
    
    - **성공 시**: 회원가입에 필요한 `verification_token`을 반환합니다.
    - 이 토큰은 10분간 유효하며, `/register/verified` API 호출 시 필수값으로 사용됩니다.
    """,
    responses={
        400: {"description": "인증 시간 만료 또는 인증 번호 불일치"}
    }
)
async def verify_email_code(request: user_schema.VerificationRequest):

    result = verification_service.verify_code(request.email, request.code)

    if result == "EXPIRED" or result is None:
        raise HTTPException(status_code=400, detail="인증 시간이 만료되었거나 잘못된 요청입니다.")
    if result == "INVALID":
        raise HTTPException(status_code=400, detail="인증 번호가 일치하지 않습니다.")

    return {"message": "인증 완료", "verification_token": result}


# ============================================================
# 이메일 인증 후 회원 가입하는 API (운영용)
# ============================================================
@router.post(
    "/register/verified",
    response_model=user_schema.UserResponse,
    summary="[운영용] 회원가입 (이메일 인증 필수)",
    description="""
    **[운영용]** 이메일 인증 토큰(`verification_token`)을 검증한 후 회원을 생성합니다.
    
    1. `/email/verify` API를 통해 토큰을 발급받아야 합니다.
    2. 토큰 내의 이메일과 입력한 이메일이 일치해야 합니다.
    3. 토큰이 만료되었거나 위조된 경우 401 에러를 반환합니다.
    """,
    responses={
        400: {"description": "이메일 불일치 또는 중복 가입"},
        401: {"description": "유효하지 않거나 만료된 토큰"}
    }
)
async def create_user_verified(
        user_in: user_schema.UserCreateVerified,
        db: Session = Depends(get_db)
):

    validation_result = verification_service.validate_signup_token(
        user_in.verification_token, user_in.email
    )

    if validation_result == "INVALID_TOKEN":
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않거나 만료되었습니다.")
    if validation_result == "WRONG_TYPE":
        raise HTTPException(status_code=401, detail="잘못된 토큰 유형입니다.")
    if validation_result == "EMAIL_MISMATCH":
        raise HTTPException(status_code=400, detail="인증된 이메일과 입력 정보가 다릅니다.")

    if user_service.check_email_exists(db, user_in.email):
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    return user_service.create_new_user(db, user_in=user_in)

# ============================================================
# 로그인 API
# ============================================================
@router.post(
    "/login",
    response_model=user_schema.Token,
    summary="로그인 (JWT 발급)",
    description="""
    이메일과 비밀번호를 사용하여 로그인합니다.
    
    - 성공 시 **Access Token**을 반환합니다.
    - 반환된 토큰은 인증이 필요한 API 요청 헤더에 `Authorization: Bearer {token}` 형태로 포함해야 합니다.
    """,
    responses={
        401: {"description": "이메일 또는 비밀번호 불일치"}
    }
)
async def login_for_access_token(
        user_in: user_schema.UserLogin,
        db: Session = Depends(get_db)
):
    access_token = user_service.authenticate_user(db, user_in=user_in)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": access_token, "token_type": "bearer"}
