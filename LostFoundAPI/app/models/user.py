from sqlalchemy import Column, String, BigInteger
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Users(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    contact_info = Column(String(255), unique=True)
    hashed_password = Column(String(255), nullable=False)

    # created_at, updated_at은 TimestampMixin에서 상속받음

    # (One-to-Many) 이 사용자가 찾아간 분실물 목록
    found_items = relationship("LostItems", back_populates="found_by_user")

    # (One-to-Many) 이 사용자에게 발급된 픽업 코드 목록
    pickup_codes = relationship("PickupCodes", back_populates="user")
