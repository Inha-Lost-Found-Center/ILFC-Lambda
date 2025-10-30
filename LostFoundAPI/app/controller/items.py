from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

import app.schemas.item as item_schema
from app.db.session import get_db
from app.models import LostItems

router = APIRouter()

# API 1.1: 전체 리스트를 가져오는 API
@router.get("/", response_model=List[item_schema.ItemResponse])
async def get_all_lost_items(
        db: Session = Depends(get_db)
):
    """
    모든 분실물 리스트를 (연관된 태그와 함께) 반환합니다.
    """

    items = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags)) # LostItems의 'tags' 관계를 조인
        .all()
    )

    return items
