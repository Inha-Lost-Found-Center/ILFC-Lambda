# LostFoundAPI/app/service/kiosk_service.py
from sqlalchemy.orm import Session
import datetime
import json
import boto3

from app.models import PickupCodes, LostItemStatus
from app.service.item_service import get_item_by_id_with_tags
from app.core.config import settings

# ==================================================
# AWS IoT Core 설정 (키오스크 공용)
# ==================================================
AWS_REGION = settings.AWS_REGION
IOT_ENDPOINT = settings.AWS_IOT_ENDPOINT

try:
    kiosk_iot_client = boto3.client(
        "iot-data",
        region_name=AWS_REGION,
        endpoint_url=IOT_ENDPOINT
    )
except Exception as e:
    print(f"Kiosk AWS IoT Client 초기화 실패: {e}")
    kiosk_iot_client = None


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


def request_item_registration(device_name: str, location: str | None):
    """
    라즈베리파이에게 분실물 등록(w/ 촬영) 요청을 전달.
    """
    if kiosk_iot_client is None:
        raise RuntimeError("AWS IoT 클라이언트가 초기화되지 않았습니다.")

    message = {
        "action": "REQUEST_REGISTER",
        "device_name": device_name,
        "meta": {
            "location": location
        }
    }

    response = kiosk_iot_client.publish(
        topic=f"locker/register/{device_name}",
        qos=1,
        payload=json.dumps(message)
    )

    return response.get("ResponseMetadata", {}).get("RequestId")
