from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import app.schemas.item as item_schema
from app.db.session import get_db
from app.service import item_service
from app.models import Users
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[item_schema.ItemResponse])
async def get_all_lost_items(
        db: Session = Depends(get_db)
):
    """
    모든 분실물 리스트를 반환합니다.
    """
    items = item_service.get_all_items_with_tags(db=db)
    return items

@router.get("/{item_id}", response_model=item_schema.ItemResponse)
async def get_item_by_id(
        item_id: int,
        db: Session = Depends(get_db)
):
    """
    지정된 ID의 단일 분실물 상세 내역을 반환합니다.
    """
    item = item_service.get_item_by_id_with_tags(db=db, item_id=item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item

# 1.4 분실물 주인 등록 API
@router.post("/{item_id}/claim", response_model=item_schema.ClaimResponse)
async def claim_lost_item(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: Users = Depends(get_current_user)
):
    """
    (인증 필요) 현재 로그인한 사용자가 특정 분실물의
    주인으로 등록(claim)합니다.
    """

    updated_data = item_service.claim_item_by_id(
        db=db, item_id=item_id, current_user=current_user
    )

    if updated_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    if updated_data == "ALREADY_CLAIMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item has already been claimed or processed."
        )

    return updated_data
