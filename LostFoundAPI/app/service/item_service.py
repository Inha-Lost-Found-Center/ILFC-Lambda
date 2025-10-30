from sqlalchemy.orm import Session, joinedload
from app.models import LostItems, Users
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
    현재 사용자가 특정 분실물을 '보관' 상태로 등록하고
    픽업 코드를 생성합니다.
    """

    item = get_item_by_id_with_tags(db, item_id=item_id)

    if not item:
        return None  # 404: 아이템 없음

    if item.status != "분실":
        # 이미 등록(보관)되었거나, 이미 찾아감(찾음)
        return "ALREADY_CLAIMED"  # 400: 이미 처리된 아이템

    item.status = "보관"
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
    (상태가 '보관' 또는 '찾음'인 아이템)
    """
    return (
        db.query(LostItems)
        .filter(LostItems.found_by_user_id == current_user.id)
        .options(joinedload(LostItems.tags))
        .all()
    )

# 1.6 나의 분실물 상세+코드 (서비스 로직)
# ------------------------------------------------------------------
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
