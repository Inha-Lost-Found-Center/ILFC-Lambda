from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import app.schemas.item as item_schema
from app.db.session import get_db
from app.service import item_service
from app.models import Users
from app.dependencies import get_current_user # 1.5 API가 사용할 의존성

router = APIRouter()

# 1.1 (GET /) - 전체 리스트
@router.get("/", response_model=List[item_schema.ItemResponse])
async def get_all_lost_items(
        db: Session = Depends(get_db)
):
    """
    모든 분실물 리스트를 반환합니다.
    """
    items = item_service.get_all_items_with_tags(db=db)
    return items

# 1.5 (GET /me) - 나의 분실물 리스트 (신규)
# (경로 순서상 /{item_id} 보다 반드시 먼저 와야 합니다)
@router.get("/me", response_model=List[item_schema.ItemResponse])
async def get_my_claimed_items(
        db: Session = Depends(get_db),
        current_user: Users = Depends(get_current_user)
):
    """
    (인증 필요) 현재 로그인한 사용자가 '주인 등록(claim)'한
    모든 분실물 리스트를 반환합니다.
    """
    # (이 로직을 app/service/item_service.py에 추가해야 합니다)
    items = item_service.get_claimed_items_by_user(
        db=db, current_user=current_user
    )
    return items

# 1.6 나의 분실물 상세+코드 확인 API
# ------------------------------------------------------------------
@router.get("/me/{item_id}", response_model=item_schema.MyItemDetailResponse)
async def get_my_claimed_item_detail(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: Users = Depends(get_current_user)
):
    """
    (인증 필요) 현재 사용자가 '주인 등록'한 특정 아이템의
    상세 정보와 픽업 코드를 (만료 시 재발급하여) 반환합니다.
    """

    data = item_service.get_my_claimed_item_details(
        db=db, item_id=item_id, current_user=current_user
    )

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    if data == "FORBIDDEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this item's code"
        )
    if data == "CODE_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find pickup code associated with this item"
        )

    return data

# 1.3 (GET /{item_id}) - 상세 내역
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

# 1.4 (POST /{item_id}/claim) - 주인 등록
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
