from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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

# 1.2 검색어 + 태그 검색 API
@router.get("/search", response_model=List[item_schema.ItemResponse])
async def search_lost_items(
        # 'q': 검색어 (선택 사항, 기본값 None)
        q: Optional[str] = Query(None, min_length=1, max_length=50),

        # 'tags': 태그 ID 리스트 (선택 사항, 기본값 None)
        #    (예: /search?tags=1&tags=3)
        tags: Optional[List[int]] = Query(None),

        db: Session = Depends(get_db)
):
    """
    (1.2) 검색어(q) 및/또는 태그(tags)로 분실물을 검색합니다.
    - q: 검색어
    - tags: 태그 ID 리스트 (여러 개 가능)
    """

    items = item_service.search_items(db=db, q=q, tags=tags)
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

# 나의 픽업 예약 취소 API
# ------------------------------------------------------------------
@router.post("/me/{item_id}/cancel", response_model=item_schema.ItemResponse)
async def cancel_my_reservation(
        item_id: int,
        cancel_data: item_schema.ReservationCancelRequest, # [추가] 취소 사유
        db: Session = Depends(get_db),
        current_user: Users = Depends(get_current_user)
):
    """
    (인증 필요) 현재 사용자가 '예약'한 픽업을 취소하고
    사유를 기록합니다. 아이템 상태는 '보관'으로 돌아갑니다.
    """

    result = item_service.cancel_reservation(
        db=db,
        item_id=item_id,
        current_user=current_user,
        cancel_reason=cancel_data.cancel_reason
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    if result == "FORBIDDEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this reservation"
        )
    if result == "NOT_RESERVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is not in 'Reserved' status"
        )
    if result in ["CODE_NOT_FOUND", "ALREADY_USED", "ALREADY_CANCELLED", "NOT_YOURS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel: {result}"
        )

    return result

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
