from sqlalchemy import Column, String, BigInteger, DateTime, Boolean, ForeignKey
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
    is_used = Column(Boolean, default=False, nullable=False)

    # 외래 키
    lost_item_id = Column(BigInteger, ForeignKey("lostitems.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


    # (Many-to-One) 이 코드를 소유한 사용자
    user = relationship("Users", back_populates="pickup_codes")

    # (One-to-One) 이 코드가 가리키는 분실물
    lost_item = relationship("LostItems", back_populates="pickup_code")
