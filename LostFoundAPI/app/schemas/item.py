from pydantic import BaseModel
import datetime
from typing import List
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
