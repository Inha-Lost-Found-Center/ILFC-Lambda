from sqlalchemy import Column, BigInteger, Numeric, ForeignKey
from .base import Base, TimestampMixin

class LostItem_Tags(Base, TimestampMixin):
    __tablename__ = "lostitem_tags"

    id = Column(BigInteger, primary_key=True, index=True)

    lost_item_id = Column(BigInteger, ForeignKey("lostitems.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    confidence = Column(Numeric(5, 2)) # (선택) 신뢰도 점수
