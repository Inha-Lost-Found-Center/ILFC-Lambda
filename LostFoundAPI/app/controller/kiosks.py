# LostFoundAPI/app/controller/kiosks.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.service import kiosk_service, locker_service
from app.schemas import item as item_schema

router = APIRouter()

# 픽업 코드 검증 및 상태 변경 요청 모델
class PickupRequest(BaseModel):
    pickup_code: str # 키오스크에 입력된 6자리 코드

# 응답 모델 (픽업 코드가 유효했을 때 반환)
class KioskPickupResponse(BaseModel):
    message: str
    item: item_schema.ItemResponse # 상태가 '찾음'으로 변경된 아이템 정보

# 사물함 닫기 요청/응답 모델
class LockerCloseRequest(BaseModel):
    pickup_code: str


class LockerCloseResponse(BaseModel):
    message: str
    locker_id: int
    device_name: str

# 픽업 코드 검증 및 아이템 상태 변경 API
@router.post(
    "/pickup",
    response_model=KioskPickupResponse,
    summary="픽업 코드 확인 및 사물함 열기",
    description=(
        "키오스크에서 손님이 입력한 6자리 픽업 코드를 검증하고 아이템을 '찾음' 상태로 갱신합니다.\n"
        "- 검증이 성공하면 할당된 사물함 번호(`item.locker_id`)와 기기(`item.device_name`)를 찾아 자동으로 사물함을 엽니다.\n"
        "- 코드가 만료되었거나 이미 사용된 경우, 상황에 맞는 HTTP 오류를 반환합니다."
    )
)
async def complete_item_pickup(
        pickup_data: PickupRequest,
        db: Session = Depends(get_db),
        background_tasks: BackgroundTasks = None
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

    locker_id = getattr(result, "locker_id", None)
    # device_name = getattr(result, "device_name", None)
    device_name = "InhaLockerPi2"
    if locker_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 분실물에 할당된 사물함 정보가 없습니다."
        )
    if not device_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 분실물에 연결된 기기 정보가 없습니다."
        )

    if background_tasks is not None:
        background_tasks.add_task(locker_service.open_locker, device_name, locker_id)
    else:
        locker_service.open_locker(device_name, locker_id)

    return {
        "message": f"픽업 코드 {pickup_data.pickup_code}가 확인되었으며, 아이템이 인계되었습니다.",
        "item": result
    }


@router.post(
    "/locker/close",
    response_model=LockerCloseResponse,
    summary="사물함 닫기 (버튼/타이머)",
    description=(
        "키오스크에서 닫기 버튼을 눌렀거나 로컬 타이머가 만료되었을 때 호출합니다.\n"
        "- 요청 본문에 픽업 코드를 전달하면 해당 아이템을 찾아 연결된 `locker_id`·`device_name`으로 IoT CLOSE 명령을 발행합니다.\n"
        "- 아이템 상태는 변경하지 않고, 문 닫기만 수행합니다."
    )
)
async def kiosk_close_locker(
        close_data: LockerCloseRequest,
        db: Session = Depends(get_db),
        background_tasks: BackgroundTasks = None
):
    """
    키오스크에서 닫기 버튼(또는 타이머 만료)을 눌렀을 때
    해당 사물함을 닫도록 IoT 명령을 발행합니다.
    """

    item = kiosk_service.fetch_item_by_pickup_code(
        db=db,
        pickup_code_str=close_data.pickup_code
    )

    if item == "INVALID_CODE":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않은 픽업 코드입니다."
        )

    locker_id = getattr(item, "locker_id", None)
    # device_name = getattr(item, "device_name", None)
    device_name = "InhaLockerPi2"

    if locker_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 분실물에 할당된 사물함 정보가 없습니다."
        )
    if not device_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 분실물에 연결된 기기 정보가 없습니다."
        )

    if background_tasks is not None:
        background_tasks.add_task(
            locker_service.close_locker,
            device_name,
            locker_id,
            close_data.pickup_code
        )
    else:
        locker_service.close_locker(device_name, locker_id, close_data.pickup_code)

    return {
        "message": f"사물함 {locker_id}번 닫기 명령이 전송되었습니다.",
        "locker_id": locker_id,
        "device_name": device_name
    }


# ==================================================
# 분실물 등록 트리거 (라즈베리파이 촬영 지시)
# ==================================================
class ItemRegisterRequest(BaseModel):
    device_name: str
    location: Optional[str] = None


@router.post(
    "/register/request",
    summary="분실물 등록 촬영 요청",
    description=(
        "키오스크에서 분실물 등록을 시작할 때 호출해 라즈베리파이(혹은 IoT 디바이스)에게 촬영/업로드를 지시합니다.\n"
        "- `device_name`은 사물함(또는 투입구)이 연결된 장비 이름, `location`은 분실물이 수거된 위치입니다.\n"
        "- 서버는 `locker/register/{device_name}` 토픽으로 MQTT 메시지를 발행하고, 응답으로 AWS Request ID를 돌려줍니다."
    )
)
async def kiosk_request_item_registration(payload: ItemRegisterRequest):
    """
    키오스크에서 라즈베리파이에게 촬영 및 업로드를 지시하는 MQTT 명령을 발행합니다.
    """
    try:
        aws_request_id = locker_service.request_item_registration(
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


class LockerOpenRequest(BaseModel):
    device_name: str
    locker_id: int | None = None
    open_chute: bool = False


class LockerOpenResponse(BaseModel):
    message: str
    locker_id: int | None
    device_name: str
    aws_request_id: str | None = None


@router.post(
    "/locker/open",
    response_model=LockerOpenResponse,
    summary="투입구/사물함 열기",
    description=(
        "키오스크에서 투입구 또는 특정 사물함을 열 때 호출합니다.\n"
        "- `open_chute=True`이면 투입구 전용 토픽(`locker/chute/{device_name}`)으로 OPEN_CHUTE 명령을 발행합니다.\n"
        "- `open_chute=False`이면 `locker_id`가 필수이며, 해당 사물함 문을 여는 MQTT 명령을 발행합니다."
    )
)
async def kiosk_open_locker(open_data: LockerOpenRequest):
    """
    키오스크에서 투입구/사물함을 열어달라고 요청할 때 호출합니다.
    """
    try:
        if open_data.open_chute:
            aws_request_id = locker_service.open_chute(open_data.device_name)
            locker_id = None
        else:
            if open_data.locker_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="open_chute=False일 때는 locker_id가 필요합니다."
                )
            aws_request_id = locker_service.open_locker(
                device_name=open_data.device_name,
                locker_id=open_data.locker_id
            )
            locker_id = open_data.locker_id
        return {
            "message": "투입구 열기 명령이 전송되었습니다." if open_data.open_chute
            else f"사물함 {open_data.locker_id}번 열기 명령이 전송되었습니다.",
            "locker_id": locker_id,
            "device_name": open_data.device_name,
            "aws_request_id": aws_request_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사물함 열기 명령 전송 실패: {str(e)}"
        )
