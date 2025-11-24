# LostFoundAPI/app/service/kiosk_service.py
from sqlalchemy.orm import Session
import datetime

from app.models import PickupCodes, LostItemStatus
from app.service.item_service import get_item_by_id_with_tags


def complete_pickup_by_code(db: Session, pickup_code_str: str):
    """
    픽업 코드를 검증하고, 유효하면 아이템 상태를 '찾음'으로 변경합니다.
    """

    # 유효하고 만료되지 않은 픽업 코드를 찾습니다.
    now = datetime.datetime.utcnow()

    pickup_code_record = db.query(PickupCodes).filter(
        PickupCodes.code == pickup_code_str,
        PickupCodes.expires_at > now,
        PickupCodes.is_used == False
    ).first()

    if not pickup_code_record:
        return "INVALID_CODE" # 404/400 (코드 없음, 만료, 이미 사용됨)

    # 아이템을 가져옵니다. (item_service 재사용)
    item = get_item_by_id_with_tags(db, item_id=pickup_code_record.lost_item_id)

    if not item:
        return "INVALID_CODE"

    if item.status == LostItemStatus.FOUND:
        return "ALREADY_PICKED_UP"

    if item.status != LostItemStatus.RESERVED:
        return "NOT_RESERVE"

    # 상태 변경 및 기록 업데이트
    item.status = LostItemStatus.FOUND
    item.found_at = now

    pickup_code_record.is_used = True

    db.commit()
    db.refresh(item)

    return item
