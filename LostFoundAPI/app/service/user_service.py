from sqlalchemy.orm import Session
from app.models import Users
from app.schemas import user as user_schema
from app.core import security

def get_user_by_email(db: Session, email: str):
    """
    이메일로 사용자를 조회합니다.
    """
    return db.query(Users).filter(Users.email == email).first()

def create_new_user(db: Session, user_in: user_schema.UserCreate):
    """
    비밀번호를 해싱하여 새 사용자를 생성합니다.
    """

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

def authenticate_user(db: Session, user_in: user_schema.UserLogin):
    """
    사용자를 인증하고, 성공 시 Access Token을 반환합니다.
    실패 시 None을 반환합니다.
    """

    user = get_user_by_email(db, email=user_in.email)

    if not user or not security.verify_password(user_in.password, user.hashed_password):
        return None

    access_token = security.create_access_token(
        data={"sub": user.email} # 'sub'는 토큰의 주체(사용자 식별자)
    )

    return access_token

def check_email_exists(db: Session, email: str) -> bool:
    """이메일 중복 여부를 확인합니다. (True: 이미 존재함)"""
    user = get_user_by_email(db, email)
    return user is not None
