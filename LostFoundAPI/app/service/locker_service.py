import json
import boto3

from app.core.config import settings

AWS_REGION = settings.AWS_REGION
IOT_ENDPOINT = settings.AWS_IOT_ENDPOINT

try:
    iot_client = boto3.client(
        "iot-data",
        region_name=AWS_REGION,
        endpoint_url=IOT_ENDPOINT
    )
except Exception as e:
    print(f"Locker AWS IoT Client 초기화 실패: {e}")
    iot_client = None


def _publish(topic: str, message: dict) -> str:
    if iot_client is None:
        raise RuntimeError("AWS IoT 클라이언트가 초기화되지 않았습니다.")

    response = iot_client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(message)
    )
    return response.get("ResponseMetadata", {}).get("RequestId")


def request_item_registration(device_name: str, location: str | None) -> str:
    message = {
        "action": "REQUEST_REGISTER",
        "device_name": device_name,
        "meta": {
            "location": location
        }
    }
    topic = f"locker/register/{device_name}"
    return _publish(topic, message)


def open_locker(device_name: str, locker_id: int) -> str:
    message = {
        "action": "OPEN",
        "locker_id": locker_id
    }
    topic = f"locker/control/{device_name}"
    return _publish(topic, message)

