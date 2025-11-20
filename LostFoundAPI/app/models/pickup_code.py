from sqlalchemy import Column, String, BigInteger, DateTime, Boolean, ForeignKey, Text  # <-- Text 추가
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import datetime

class PickupCodes(Base, TimestampMixin):
    __tablename__ = "pickupcodes"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(6), unique=True, nullable=False, index=True)

    # Mixin의 created_at과 별개인, 코드 '생성' 및 '만료' 시각
    generated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False) # (유지)

    # 취소 관련 필드
    cancelled_at = Column(DateTime, nullable=True)  # '취소됨' 상태가 된 시각 (NULL 허용)
    cancel_reason = Column(Text, nullable=True)     # '취소됨' 상태가 된 사유 (NULL 허용)

    # 외래 키
    lost_item_id = Column(BigInteger, ForeignKey("lostitems.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


    # (Many-to-One) 이 코드를 소유한 사용자
    user = relationship("Users", back_populates="pickup_codes")

    lost_item = relationship("LostItems", back_populates="pickup_codes")
