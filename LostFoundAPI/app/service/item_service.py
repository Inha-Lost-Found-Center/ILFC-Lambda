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
