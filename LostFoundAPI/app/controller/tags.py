from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.tag import TagResponse
from app.service import tag_service

router = APIRouter()

@router.get("/", response_model=List[TagResponse])
async def get_all_tags(
        db: Session = Depends(get_db)
):
    """
    DB에 저장된 모든 태그 리스트를 반환합니다.
    """
    tags = tag_service.get_all_tags(db=db)
    return tags
