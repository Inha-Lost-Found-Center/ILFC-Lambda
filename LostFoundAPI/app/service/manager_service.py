from sqlalchemy.orm import Session
from app.models.manager import Managers
from app.core import security
from app.schemas.manager import ManagerLogin

def get_manager_by_email(db: Session, email: str):
    return db.query(Managers).filter(Managers.email == email).first()

def authenticate_manager(db: Session, login_data: ManagerLogin):
    """
    이메일과 비밀번호를 검증하여 관리자 객체를 반환합니다.
    실패 시 None 반환.
    """
    manager = get_manager_by_email(db, login_data.email)

    if not manager:
        return None

    if not security.verify_password(login_data.password, manager.hashed_password):
        return None

    return manager
