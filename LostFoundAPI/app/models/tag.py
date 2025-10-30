from sqlalchemy import Column, String, BigInteger
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Tags(Base, TimestampMixin):
    __tablename__ = "tags"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)

    # (LostItems와의 M2M 관계)
    lost_items = relationship(
        "LostItems",
        secondary="lostitem_tags",
        back_populates="tags"
    )
