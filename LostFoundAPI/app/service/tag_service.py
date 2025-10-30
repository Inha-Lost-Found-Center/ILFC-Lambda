from sqlalchemy.orm import Session
from app.models import Tags

def get_all_tags(db: Session):
    """
    DB에 저장된 모든 태그 리스트를 조회합니다.
    """
    return db.query(Tags).all()
