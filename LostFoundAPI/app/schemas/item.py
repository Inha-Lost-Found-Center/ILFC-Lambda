from pydantic import BaseModel
import datetime
from typing import List, Optional
from .tag import TagResponse
from .pickup_code import PickupCodeResponse

# Item 응답 스키마
class ItemResponse(BaseModel):
    id: int
    photo_url: str
    location: str | None = None
    status: str
    registered_at: datetime.datetime

    tags: List[TagResponse] = []

    class Config:
        from_attributes = True

# 1.4 API를 위한 전용 응답 스키마
class ClaimResponse(BaseModel):
    item: ItemResponse
    pickup_code: PickupCodeResponse

# 1.6 '나의 분실물 상세' 응답 스키마
# (1.4의 ClaimResponse와 구조가 동일함)
# ------------------------------------------------------------------
class MyItemDetailResponse(BaseModel):
    item: ItemResponse
    pickup_code: PickupCodeResponse

# 픽업 예약 취소 요청 스키마
# ------------------------------------------------------------------
class ReservationCancelRequest(BaseModel):
    cancel_reason: str # 사용자가 입력하는 취소 사유

# 관리자용 분실물 수동 등록 스키마
class ItemCreate(BaseModel):
    photo_url: str
    device_name: Optional[str] = "ManualRegister" # 기본값
    location: str
    description: str
    tags: List[str] = []  # 태그 이름 리스트 (예: ["지갑", "검정색"])
