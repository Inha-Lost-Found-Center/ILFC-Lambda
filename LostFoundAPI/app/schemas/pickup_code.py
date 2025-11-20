from typing import Optional
from pydantic import BaseModel
import datetime

class PickupCodeResponse(BaseModel):
    code: str
    expires_at: datetime.datetime

    class Config:
        from_attributes = True

# 관리자용 픽업 로그 상세 응답 스키마
class PickupLogResponse(BaseModel):
    id: int
    code: str
    is_used: bool
    generated_at: datetime.datetime
    expires_at: datetime.datetime
    cancelled_at: Optional[datetime.datetime] = None
    cancel_reason: Optional[str] = None

    user_email: str       # 사용자 이메일
    item_description: str # 아이템 설명
    item_id: int

    class Config:
        from_attributes = True
