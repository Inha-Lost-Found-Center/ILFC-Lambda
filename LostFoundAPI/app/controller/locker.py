from fastapi import APIRouter, HTTPException, status
from app.service import locker_service

router = APIRouter()


# ==================================================
# 사물함 열기 요청
# ==================================================
@router.post("/open/{locker_id}", summary="사물함 원격 열기")
async def open_smart_locker(locker_id: int, device_name: str):
    """
    AWS IoT Core(MQTT)를 통해 라즈베리파이에 '문 열기' 명령을 전송합니다.

    - **locker_id**: 제어할 사물함 번호 (1 ~ 4)
    - **device_name**: 사물함이 연결된 라즈베리파이/키오스크 이름
    - 이 API는 Swagger UI에서 테스트 버튼을 누르면 바로 실행됩니다.
    """

    try:
        aws_request_id = locker_service.open_locker(device_name=device_name, locker_id=locker_id)

        return {
            "status": "success",
            "message": f"사물함 {locker_id}번 열기 명령 전송 완료",
            "locker_id": locker_id,
            "aws_request_id": aws_request_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"명령 전송 실패: {str(e)}"
        )
