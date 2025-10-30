from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

import app.schemas.item as item_schema
from app.db.session import get_db
from app.models import LostItems

router = APIRouter()

# 1.1 전체 리스트 API
@router.get("/", response_model=List[item_schema.ItemResponse])
async def get_all_lost_items(
        db: Session = Depends(get_db)
):
    """
    모든 분실물 리스트를 (연관된 태그와 함께) 반환합니다.
    """
    items = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags))
        .all()
    )
    return items

# 1.3 분실물 상세 내역 보기 API
@router.get("/{item_id}", response_model=item_schema.ItemResponse)
async def get_item_by_id(
        item_id: int,
        db: Session = Depends(get_db)
):
    """
    지정된 ID의 단일 분실물 상세 내역을 (태그 포함) 반환합니다.
    """

    item = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags)) # 태그 정보도 JOIN
        .filter(LostItems.id == item_id)     # ID로 필터링
        .first()                             # 첫 번째 결과(또는 None)
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item
