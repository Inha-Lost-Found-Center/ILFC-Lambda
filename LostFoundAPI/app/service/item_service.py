from sqlalchemy.orm import Session, joinedload
from app.models import LostItems, Users, Tags, LostItem_Tags, LostItemStatus, PickupCodes
from typing import List, Optional
import datetime
from app.service import pickup_code_service
from app.service import tag_service

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
    item = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags), joinedload(LostItems.pickup_codes))
        .filter(LostItems.id == item_id)
        .first()
    )

    if not item:
        return None  # 404: 아이템 없음

    if item.status != LostItemStatus.STORAGE:
        return "ALREADY_CLAIMED"  # 400

    item.status = LostItemStatus.RESERVED
    item.found_by_user_id = current_user.id

    new_code = pickup_code_service.create_pickup_code(
        db=db, item=item, user=current_user
    )

    db.commit()
    db.refresh(item)
    db.refresh(new_code)

    return {"item": item, "pickup_code": new_code}

def get_claimed_items_by_user(db: Session, current_user: Users):
    """
    나의 분실물 리스트 조회
    """
    return (
        db.query(LostItems)
        .filter(LostItems.found_by_user_id == current_user.id)
        .options(joinedload(LostItems.tags))
        .all()
    )

def get_my_claimed_item_details(db: Session, item_id: int, current_user: Users):
    """
    나의 분실물 상세 + 픽업 코드 확인
    """
    item = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags), joinedload(LostItems.pickup_codes))
        .filter(LostItems.id == item_id)
        .first()
    )

    if not item: return None
    if item.found_by_user_id != current_user.id: return "FORBIDDEN"

    pickup_code = item.pickup_code
    if not pickup_code:
        return "CODE_NOT_FOUND"

    if pickup_code.expires_at <= datetime.datetime.utcnow():
        print(f"Pickup code {pickup_code.code} expired. Reissuing...")

        new_code_str = pickup_code_service.generate_unique_code(db)
        new_expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)

        # 만료 시 갱신 (새 코드를 생성하지 않고 기존 최신 코드를 연장)
        pickup_code.code = new_code_str
        pickup_code.expires_at = new_expires_at
        pickup_code.generated_at = datetime.datetime.utcnow()
        pickup_code.is_used = False

        db.commit()
        db.refresh(pickup_code)

    return {"item": item, "pickup_code": pickup_code}

def search_items(db: Session, q: Optional[str], tags: Optional[List[int]]):
    query = (
        db.query(LostItems)
        .options(joinedload(LostItems.tags))
    )
    if q:
        search_query = f"%{q}%"
        query = query.filter(
            (LostItems.description.ilike(search_query)) |
            (LostItems.location.ilike(search_query))
        )
    if tags:
        query = query.join(LostItem_Tags).filter(LostItem_Tags.tag_id.in_(tags))

    query = query.group_by(LostItems.id)
    return query.all()

def cancel_reservation(db: Session, item_id: int, current_user: Users, cancel_reason: str):
    """
    예약 취소 (이력 보존)
    """
    item = db.query(LostItems).options(
        joinedload(LostItems.pickup_codes)
    ).filter(LostItems.id == item_id).first()

    if not item: return None
    if item.found_by_user_id != current_user.id: return "FORBIDDEN"
    if item.status != LostItemStatus.RESERVED: return "NOT_YOURS"

    # 가장 최신의 유효한 코드를 찾음
    pickup_code = (
        db.query(PickupCodes)
        .filter(
            PickupCodes.lost_item_id == item_id,
            PickupCodes.is_used == False,
            PickupCodes.cancelled_at == None
        )
        .order_by(PickupCodes.id.desc())
        .first()
    )

    if not pickup_code: return "CODE_NOT_FOUND"

    now = datetime.datetime.utcnow()

    # 취소 처리 (이력 남기기)
    pickup_code.cancelled_at = now
    pickup_code.cancel_reason = cancel_reason
    pickup_code.is_used = True;

    # 아이템 상태 원복
    item.status = LostItemStatus.STORAGE
    item.found_by_user_id = None
    item.found_at = None

    db.commit()
    db.refresh(item)
    db.refresh(pickup_code)

    return item

# 분실물 수동 생성 로직
def create_lost_item(db: Session, item_in):
    new_item = LostItems(
        photo_url=item_in.photo_url,
        device_name=item_in.device_name,
        location=item_in.location,
        description=item_in.description,
        status=LostItemStatus.STORAGE
    )

    for tag_name in item_in.tags:
        tag = tag_service.get_or_create_tag(db, tag_name)
        new_item.tags.append(tag)

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item
