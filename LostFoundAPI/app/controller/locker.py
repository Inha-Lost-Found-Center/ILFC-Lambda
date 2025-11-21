from fastapi import APIRouter, HTTPException, status
import boto3
import json
from app.core.config import settings

router = APIRouter()

# ==================================================
# AWS IoT Core 설정
# ==================================================
AWS_REGION = settings.AWS_REGION
IOT_ENDPOINT = settings.AWS_IOT_ENDPOINT

# 3. Boto3 클라이언트 생성
try:
    iot_client = boto3.client(
        'iot-data',
        region_name=AWS_REGION,
        endpoint_url=IOT_ENDPOINT
    )
except Exception as e:
    print(f"AWS IoT Client 초기화 실패: {e}")
    iot_client = None


# ==================================================
# 사물함 열기 요청
# ==================================================
@router.post("/open/{locker_id}", summary="사물함 원격 열기")
async def open_smart_locker(locker_id: int):
    """
    AWS IoT Core(MQTT)를 통해 라즈베리파이에 '문 열기' 명령을 전송합니다.

    - **locker_id**: 제어할 사물함 번호 (1 ~ 4)
    - 이 API는 Swagger UI에서 테스트 버튼을 누르면 바로 실행됩니다.
    """

    if iot_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS IoT 클라이언트가 초기화되지 않았습니다."
        )

    payload = {
        "locker_id": locker_id
    }

    try:
        # MQTT 메시지 게시 (Publish)
        response = iot_client.publish(
            topic="locker/control",
            qos=1,  # QoS 1: 최소 1회 전달 보장
            payload=json.dumps(payload)
        )

        return {
            "status": "success",
            "message": f"사물함 {locker_id}번 열기 명령 전송 완료",
            "locker_id": locker_id,
            "aws_request_id": response.get('ResponseMetadata', {}).get('RequestId')
        }

    except Exception as e:
        print(f"MQTT 전송 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"명령 전송 실패: {str(e)}"
        )
