from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.service import dev_service
from app.schemas.item import ItemResponse # (기존 응답 스키마 재사용)

router = APIRouter()

@router.post("/create-dummy-items", response_model=List[ItemResponse])
async def generate_dummy_items(
        count: int = Query(10, gt=0, le=50), # 1~50개 사이로 개수 제한
        db: Session = Depends(get_db)
):
    """
    테스트용 가상 분실물을 생성합니다. (개발용, 실제로 절대 쓰지 마세요.)
    - count: 생성할 아이템 개수 (기본 10, 최대 50)
    """
    try:
        created_items = dev_service.create_dummy_items(db, count)
        return created_items
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 데이터 생성 실패: {str(e)}"
        )


@router.delete("/delete-dummy-items", summary="테스트용 더미 데이터 삭제")
async def delete_dummy_items(
        db: Session = Depends(get_db)
):
    """
    device_name이 'TestAPI-Generator'인 테스트 데이터(아이템 및 관련 픽업 코드)를 삭제합니다.
    """
    try:
        deleted_count = dev_service.delete_dummy_items(db)
        return {"deleted_items": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 데이터 삭제 실패: {str(e)}"
        )