from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core import security
from app.dependencies import get_current_admin
from app.models.manager import Managers

from app.service import manager_service
from app.service import tag_service, item_service, pickup_code_service

from app.schemas import manager as manager_schema
from app.schemas import user as user_schema
from app.schemas import tag as tag_schema
from app.schemas import item as item_schema
from app.schemas import pickup_code as pickup_schema

router = APIRouter()

# ============================================================
# 0. 관리자 인증
# ============================================================

@router.post("/login", response_model=user_schema.Token)
async def login_admin(
        login_data: manager_schema.ManagerLogin,
        db: Session = Depends(get_db)
):
    manager = manager_service.authenticate_manager(db, login_data)

    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": manager.email, "role": "admin"}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=manager_schema.ManagerResponse)
async def read_admin_me(
        current_admin: Managers = Depends(get_current_admin)
):
    return current_admin


# ============================================================
# 1. 태그 관리 (Tag Management) - 관리자 권한 필요
# ============================================================

@router.post("/tags", response_model=tag_schema.TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
        tag_in: tag_schema.TagCreate,
        db: Session = Depends(get_db),
        current_admin: Managers = Depends(get_current_admin) # 관리자 권한 체크
):
    """[관리자] 새로운 태그를 생성합니다."""
    if tag_service.get_tag_by_name(db, tag_in.name):
        raise HTTPException(status_code=400, detail="이미 존재하는 태그입니다.")
    return tag_service.create_tag(db, tag_in.name)

@router.put("/tags/{tag_id}", response_model=tag_schema.TagResponse)
async def update_tag(
        tag_id: int,
        tag_in: tag_schema.TagUpdate,
        db: Session = Depends(get_db),
        current_admin: Managers = Depends(get_current_admin)
):
    """[관리자] 태그 이름을 수정합니다."""
    updated_tag = tag_service.update_tag(db, tag_id, tag_in.name)
    if not updated_tag:
        raise HTTPException(status_code=404, detail="태그를 찾을 수 없습니다.")
    return updated_tag

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
        tag_id: int,
        db: Session = Depends(get_db),
        current_admin: Managers = Depends(get_current_admin)
):
    """[관리자] 태그를 삭제합니다."""
    success = tag_service.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="태그를 찾을 수 없습니다.")
    return None


# ============================================================
# 2. 분실물 수동 등록 (Manual Item Registration) - 관리자 권한 필요
# ============================================================

@router.post("/items", response_model=item_schema.ItemResponse, status_code=status.HTTP_201_CREATED)
async def register_lost_item(
        item_in: item_schema.ItemCreate,
        db: Session = Depends(get_db),
        current_admin: Managers = Depends(get_current_admin)
):
    """
    [관리자] 분실물을 수동으로 등록합니다.
    - photo_url: S3 등에 업로드된 이미지 주소
    - tags: 태그 이름 리스트 (예: ["지갑", "가죽"]) -> 없으면 자동 생성됨
    """
    return item_service.create_lost_item(db, item_in)


# ============================================================
# 3. 픽업 코드 로그 조회 (Pickup Log Lookup) - 관리자 권한 필요
# ============================================================

@router.get("/pickup-logs", response_model=List[pickup_schema.PickupLogResponse])
async def get_pickup_logs(
        db: Session = Depends(get_db),
        current_admin: Managers = Depends(get_current_admin)
):
    """
    [관리자] 모든 픽업 코드 발급 및 사용 이력을 조회합니다.
    """
    logs = pickup_code_service.get_all_pickup_logs(db)

    result = []
    for log in logs:
        user_email = log.user.email if log.user else "Deleted User"
        item_desc = log.lost_item.description if log.lost_item else "Deleted Item"

        result.append(pickup_schema.PickupLogResponse(
            id=log.id,
            code=log.code,
            is_used=log.is_used,
            generated_at=log.generated_at,
            expires_at=log.expires_at,
            cancelled_at=log.cancelled_at,
            cancel_reason=log.cancel_reason,
            user_email=user_email,
            item_description=item_desc,
            item_id=log.lost_item_id
        ))

    return result
