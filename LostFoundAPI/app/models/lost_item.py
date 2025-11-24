import enum
from sqlalchemy import Column, String, BigInteger, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import datetime

class LostItemStatus(str, enum.Enum):
    STORAGE = "보관"
    RESERVED = "예약"
    FOUND = "찾음"
    LOST = "분실"

class LostItems(Base, TimestampMixin):
    __tablename__ = "lostitems"

    id = Column(BigInteger, primary_key=True, index=True)
    photo_url = Column(String(2048), nullable=False)
    device_name = Column(String(255))
    location = Column(String(255), index=True)
    locker_id = Column(BigInteger, nullable=True, index=True)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    description = Column(Text)

    status = Column(
        Enum(LostItemStatus,
             name="lost_item_status",
             create_type=False,
             native_enum=False,
             values_callable=lambda obj: [e.value for e in obj]
             ),
        default=LostItemStatus.STORAGE,
        nullable=False
    )

    found_at = Column(DateTime)

    # 외래 키 정의 (ondelete="SET NULL": 유저가 삭제되어도 분실물 기록은 남김)
    found_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))

    # created_at, updated_at은 TimestampMixin에서 상속받음

    tags = relationship(
        "Tags",
        secondary="lostitem_tags",
        back_populates="lost_items"
    )

    found_by_user = relationship("Users", back_populates="found_items")

    pickup_codes = relationship(
        "PickupCodes",
        back_populates="lost_item",
        order_by="desc(PickupCodes.id)"
    )

    @property
    def pickup_code(self):
        return self.pickup_codes[0] if self.pickup_codes else None
