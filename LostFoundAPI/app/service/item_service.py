from sqlalchemy.orm import Session, joinedload
from app.models import LostItems, Users, Tags, LostItem_Tags, LostItemStatus
from typing import List, Optional
import datetime
from app.service import pickup_code_service

def get_all_items_with_tags(db: Session):
    """
    모든 분실물 리스트를 (연관된 태그와 함께) 조회합니다.
    """
    return (
        db.query(LostItems)
        .options(joinedload(LostItems.tags))
        .all()
    )

def get_item_by_id_with_tags(db: Session, item_id: int):
    """
    ID로 단일 분실물을 (연관된 태그와 함께) 조회합니다.
    """
    return (
        db.query(LostItems)
        .options(joinedload(LostItems.tags))
        .filter(LostItems.id == item_id)
        .first()
    )

def claim_item_by_id(db: Session, item_id: int, current_user: Users):
    """
    현재 사용자가 특정 분실물을 '보관'에서 '예약' 상태로 등록하고
    픽업 코드를 생성합니다.
    """

    item = get_item_by_id_with_tags(db, item_id=item_id)

    if not item:
        return None  # 404: 아이템 없음

    if item.status != LostItemStatus.STORAGE:
        # 이미 예약되었거나, 이미 찾아감(찾음)
        return "ALREADY_CLAIMED"  # 400: 이미 처리된 아이템

    item.status = LostItemStatus.RESERVED
    item.found_by_user_id = current_user.id

    new_code = pickup_code_service.create_pickup_code(
        db=db, item=item, user=current_user
    )

    db.commit()
    db.refresh(item)
    db.refresh(new_code)

    return {"item": item, "pickup_code": new_code}

# 1.5 나의 분실물 리스트 확인 (서비스 로직)
def get_claimed_items_by_user(db: Session, current_user: Users):
    """
    현재 사용자가 '주인 등록(claim)'한 모든 분실물 리스트를 조회합니다.
    (상태가 '예약' 또는 '찾음'인 아이템)
    """
    return (
        db.query(LostItems)
        .filter(LostItems.found_by_user_id == current_user.id)
        .options(joinedload(LostItems.tags))
        .all()
    )

# 1.6 나의 분실물 상세+코드 (서비스 로직)
def get_my_claimed_item_details(db: Session, item_id: int, current_user: Users):
    """
    현재 사용자가 '주인 등록'한 특정 아이템의 상세 정보와
    픽업 코드를 (필요시 재발급하여) 반환합니다.
    """

    item = get_item_by_id_with_tags(db, item_id=item_id)

    if not item:
        return None # 404 Not Found

    if item.found_by_user_id != current_user.id:
        return "FORBIDDEN" # 403 Forbidden

    pickup_code = item.pickup_code
    if not pickup_code:
        return "CODE_NOT_FOUND" # 500 Internal Error

    if pickup_code.expires_at <= datetime.datetime.utcnow():
        # 코드가 만료됨! 새 코드로 재발급
        print(f"Pickup code {pickup_code.code} expired. Reissuing...")

        new_code_str = pickup_code_service.generate_unique_code(db)
        new_expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)

        pickup_code.code = new_code_str
        pickup_code.expires_at = new_expires_at
        pickup_code.generated_at = datetime.datetime.utcnow()
        pickup_code.is_used = False # (혹시 모르니 초기화)

        db.commit()
        db.refresh(pickup_code)

    return {"item": item, "pickup_code": pickup_code}

# 1.2 (신규) 검색어 + 태그 검색 (서비스 로직)
def search_items(db: Session, q: Optional[str], tags: Optional[List[int]]):
    """
    검색어(q)와 태그 ID 리스트(tags)로 분실물을 검색합니다.
    """

    query = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags)) # 항상 태그 정보를 포함 (N+1 방지)
    )

    # [검색어] q가 존재하면, 'description' 또는 'location'에서 검색
    if q:
        search_query = f"%{q}%"
        # (참고) 검색할 컬럼 추가 가능 (예: device_name)
        query = query.filter(
            (LostItems.description.ilike(search_query)) |
            (LostItems.location.ilike(search_query))
        )

    # [태그] tags 리스트가 존재하면, 해당 태그 ID를 모두 포함하는 아이템 검색
    if tags:
        # LostItems가 LostItem_Tags를 통해 Tags와 연결되므로,
        # LostItem_Tags 테이블을 명시적으로 조인해야 함
        query = query.join(LostItem_Tags).filter(LostItem_Tags.tag_id.in_(tags))

    # '분실' 상태인 것만 검색 -> 현재 모든 품목이 검색되도록 함.
    # query = query.filter(LostItems.status.in_(["보관"]))
    
    query = query.group_by(LostItems.id)

    return query.all()


# [추가] 픽업 예약 취소 (서비스 로직)
# ------------------------------------------------------------------
def cancel_reservation(db: Session, item_id: int, current_user: Users, cancel_reason: str):
    """
    현재 사용자가 '예약'한 분실물에 대해 픽업을 취소하고
    상태를 '보관'으로 되돌립니다.
    """

    item = db.query(LostItems).options(
        joinedload(LostItems.pickup_code)
    ).filter(LostItems.id == item_id).first()

    if not item:
        return None  # 404: 아이템 없음

    if item.found_by_user_id != current_user.id:
        return "FORBIDDEN"  # 403: 권한 없음

    if item.status != LostItemStatus.RESERVED:
        # '보관' 상태이거나, 이미 '찾음' 상태일 수 있음
        return "NOT_YOURS"  # 400: 보관 상태가 아님

    pickup_code = item.pickup_code

    if not pickup_code:
        return "CODE_NOT_FOUND" # 500: 예약 상태인데 코드가 없음

    if pickup_code.is_used:
        return "ALREADY_USED" # 400: 이미 사용된 코드

    if pickup_code.cancelled_at is not None:
        return "ALREADY_CANCELLED" # 400: 이미 취소된 코드

    now = datetime.datetime.utcnow()

    # PickupCodes 업데이트 (취소 사유 및 시각 기록)
    pickup_code.cancelled_at = now
    pickup_code.cancel_reason = cancel_reason
    pickup_code.is_used = True;

    # LostItems 업데이트 (상태 되돌리기)
    item.status = LostItemStatus.STORAGE
    item.found_by_user_id = None
    item.found_at = None

    # 8. DB 커밋 및 반환
    db.commit()
    db.refresh(item)
    db.refresh(pickup_code)

    return item
