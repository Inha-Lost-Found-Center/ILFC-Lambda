# LostFoundAPI/app/controller/kiosks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.service import kiosk_service
from app.schemas import item as item_schema

router = APIRouter()

# 픽업 코드 검증 및 상태 변경 요청 모델
class PickupRequest(BaseModel):
    pickup_code: str # 키오스크에 입력된 6자리 코드

# 응답 모델 (픽업 코드가 유효했을 때 반환)
class KioskPickupResponse(BaseModel):
    message: str
    item: item_schema.ItemResponse # 상태가 '찾음'으로 변경된 아이템 정보

# 픽업 코드 검증 및 아이템 상태 변경 API
@router.post("/pickup", response_model=KioskPickupResponse)
async def complete_item_pickup(
        pickup_data: PickupRequest,
        db: Session = Depends(get_db)
):
    """
    (키오스크 전용) 픽업 코드를 검증하고, 유효하면 해당 분실물의 상태를
    '보관'에서 '찾음'으로 변경합니다.
    """

    # 서비스 로직 호출
    result = kiosk_service.complete_pickup_by_code(
        db=db,
        pickup_code_str=pickup_data.pickup_code
    )

    if result == "INVALID_CODE":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않거나 만료된 픽업 코드입니다."
        )
    if result == "ALREADY_PICKED_UP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 '찾음' 처리된 분실물입니다."
        )
    if result == "NOT_IN_STORAGE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="보관 상태가 아닌 분실물입니다. (분실 상태이거나, 다른 상태)"
        )

    return {
        "message": f"픽업 코드 {pickup_data.pickup_code}가 확인되었으며, 아이템이 인계되었습니다.",
        "item": result
    }


# ==================================================
# 분실물 등록 트리거 (라즈베리파이 촬영 지시)
# ==================================================
class ItemRegisterRequest(BaseModel):
    device_name: str
    location: Optional[str] = None


@router.post("/register/request", summary="키오스크 → IoT 분실물 등록 요청")
async def kiosk_request_item_registration(payload: ItemRegisterRequest):
    """
    키오스크에서 라즈베리파이에게 촬영 및 업로드를 지시하는 MQTT 명령을 발행합니다.
    """
    try:
        aws_request_id = kiosk_service.request_item_registration(
            device_name=payload.device_name,
            location=payload.location
        )
        return {
            "status": "queued",
            "device_name": payload.device_name,
            "aws_request_id": aws_request_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"등록 명령 전송 실패: {str(e)}"
        )
