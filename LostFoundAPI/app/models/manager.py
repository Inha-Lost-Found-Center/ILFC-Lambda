from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, Enum
from .base import Base, TimestampMixin
import enum
import datetime

class ManagerRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"

class Managers(Base, TimestampMixin):
    __tablename__ = "managers"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)

    role = Column(
        Enum(ManagerRole, native_enum=False, length=20),
        default=ManagerRole.STAFF,
        nullable=False
    )

    is_active = Column(Boolean, default=True, nullable=False)
    refresh_token = Column(String(255), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
