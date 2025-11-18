import enum
from sqlalchemy import Column, String, BigInteger, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import datetime

class LostItemStatus(str, enum.Enum):
    STORAGE = "보관"
    RESERVED = "예약"
    FOUND = "찾음"

class LostItems(Base, TimestampMixin):
    __tablename__ = "lostitems"

    id = Column(BigInteger, primary_key=True, index=True)
    photo_url = Column(String(2048), nullable=False)
    device_name = Column(String(255))
    location = Column(String(255), index=True)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    description = Column(Text)
    status = Column(String(50), default='보관', nullable=False)
    found_at = Column(DateTime)

    # 외래 키 정의 (ondelete="SET NULL": 유저가 삭제되어도 분실물 기록은 남김)
    found_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))

    # created_at, updated_at은 TimestampMixin에서 상속받음

    # (M2M) 태그 관계 (기존)
    tags = relationship(
        "Tags",
        secondary="lostitem_tags",
        back_populates="lost_items"
    )

    # (신규) (Many-to-One) 이 아이템을 찾아간 사용자
    found_by_user = relationship("Users", back_populates="found_items")

    # (신규) (One-to-One) 이 아이템에 발급된 픽업 코드
    # uselist=False로 One-to-One 관계를 명시
    pickup_code = relationship("PickupCodes", back_populates="lost_item", uselist=False)
